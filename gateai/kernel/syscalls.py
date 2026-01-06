"""
GateAI Kernel Syscalls v1.0

OS-grade system calls for kernel space operations.
This is the ONLY legal entry point from User Space into Kernel Space.

Syscalls are:
- Deterministic (same inputs → same outputs)
- Physically safe (survive PostgreSQL concurrency)
- ABI-compliant (use kernel.abi classifiers)
- Auditable (KernelAuditLog always exists)
- Broken-transaction safe (no queries inside failed atomic blocks)
- Re-entrant safe (same owner can re-enter)
- Domain-agnostic (kernel-level only)

NO BUSINESS LOGIC IMPORTS ALLOWED.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from django.db import transaction, IntegrityError
from django.db.transaction import get_connection
from django.utils import timezone

from kernel.abi import classify_success, classify_failure, map_outcome_to_status, KernelOutcome, KernelErrorCode
from kernel.idempotency_primitives import claim_idempotency_key
from kernel.models import KernelAuditLog
from decision_slots.models import ResourceLock

logger = logging.getLogger(__name__)


@dataclass
class SyscallResult:
    """
    Result of a kernel syscall execution.
    
    Fields:
        audit_id: Trace ID for this syscall (maps to KernelAuditLog.event_id)
        outcome: Full outcome dict (serialized KernelOutcome)
        outcome_code: Quick status accessor (OK/REPLAY/CONFLICT/etc.)
    """
    audit_id: str
    outcome: dict
    outcome_code: str


def _parse_expires_at(payload: Dict[str, Any]) -> datetime:
    """
    Extract or compute expires_at from payload.
    
    STDLIB-ONLY time parsing (no dateutil).
    
    Supports:
    - expires_at: datetime object (direct)
    - expires_at: ISO-8601 string via datetime.fromisoformat()
    - duration_seconds: int (compute from now)
    
    Args:
        payload: Syscall payload
    
    Returns:
        datetime for lock expiration
    
    Raises:
        ValueError: if neither expires_at nor duration_seconds provided, or invalid format
    """
    if "expires_at" in payload:
        expires_at = payload["expires_at"]
        
        # Accept datetime objects directly
        if isinstance(expires_at, datetime):
            return expires_at
        
        # Parse ISO-8601 strings (stdlib only)
        if isinstance(expires_at, str):
            try:
                # Normalize 'Z' suffix to '+00:00' for fromisoformat()
                fixed = expires_at.replace("Z", "+00:00") if expires_at.endswith("Z") else expires_at
                expires_at = datetime.fromisoformat(fixed)
                return expires_at
            except ValueError as e:
                raise ValueError(f"Invalid ISO-8601 datetime string: {payload['expires_at']} ({e})")
        
        raise ValueError(f"expires_at must be datetime or ISO-8601 string, got {type(expires_at)}")
    
    if "duration_seconds" in payload:
        duration = int(payload["duration_seconds"])
        return timezone.now() + timedelta(seconds=duration)
    
    raise ValueError("Payload must include 'expires_at' or 'duration_seconds'")


def _validate_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Validate syscall payload has required fields.
    
    Args:
        payload: Syscall payload
    
    Returns:
        Error message if invalid, None if valid
    """
    required_fields = [
        "decision_id",
        "context_hash",
        "resource_type",
        "resource_id",
        "owner_id",
    ]
    
    missing = [field for field in required_fields if field not in payload]
    
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    
    # Check expires_at or duration_seconds
    if "expires_at" not in payload and "duration_seconds" not in payload:
        return "Payload must include 'expires_at' or 'duration_seconds'"
    
    return None


def _sanitize_payload_for_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize payload for JSON storage in KernelAuditLog.
    
    Guarantees:
    - datetime -> isoformat()
    - primitives (int/float/str/bool/None) -> unchanged
    - everything else -> fallback to str(v)
    """
    sanitized = {}
    for k, v in payload.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            sanitized[k] = v
        elif hasattr(v, 'isoformat'):  # Handles datetime and similar
            sanitized[k] = v.isoformat()
        else:
            sanitized[k] = str(v)
    return sanitized


def _create_audit_root(payload: Dict[str, Any]) -> KernelAuditLog:
    """
    Create audit root (PID equivalent) for syscall.
    
    This MUST be created before any CAS/lock attempt.
    Even if syscall crashes, this audit must exist.
    
    Args:
        payload: Syscall payload
    
    Returns:
        KernelAuditLog entry (PENDING status)
    """
    event_id = uuid.uuid4()
    
    audit = KernelAuditLog.objects.create(
        event_id=event_id,
        event_type="SYS_CLAIM",
        decision_id=str(payload.get("decision_id", "unknown")),
        idempotency_key=f"sys_claim:{payload.get('decision_id')}:{payload.get('context_hash')}",
        context_hash=str(payload.get("context_hash", "")),
        schema_version="1.0",
        payload={"request": _sanitize_payload_for_audit(payload)},
        status="EMITTED",  # PENDING equivalent - syscall in flight
    )
    
    logger.info(
        "SYS_CLAIM: Audit root allocated",
        extra={
            "audit_id": str(audit.event_id),
            "decision_id": payload.get("decision_id"),
            "resource_type": payload.get("resource_type"),
            "resource_id": payload.get("resource_id"),
        },
    )
    
    return audit


def _update_audit(audit: KernelAuditLog, outcome: KernelOutcome) -> None:
    """
    Update audit log with outcome (best-effort, never blocks syscall).
    
    CRITICAL: This MUST NEVER raise exceptions or affect syscall return.
    Audit is best-effort - syscall correctness takes precedence.
    
    Args:
        audit: Audit log entry to update
        outcome: KernelOutcome to store
    """
    try:
        # Store outcome in payload (best-effort)
        KernelAuditLog.store_outcome(audit.event_id, outcome)
        
        # Map outcome to status
        status = map_outcome_to_status(outcome)
        
        # Update status (safe mark, best-effort)
        KernelAuditLog.safe_mark_handled(
            event_id=audit.event_id,
            status=status,
        )
        
    except Exception as e:
        # SWALLOW ALL ERRORS - audit failure must not block syscall
        logger.error(
            "SYS_CLAIM: Audit closure failed (swallowed, syscall proceeds)",
            extra={
                "audit_id": str(audit.event_id),
                "outcome_code": outcome.outcome_code,
                "error": str(e),
            },
            exc_info=True,
        )


def _cleanup_expired_lock(resource_type: str, resource_id: Any) -> bool:
    """
    Best-effort cleanup of expired lock (shadow pre-check).
    
    Deletes stale lock if found, reducing false conflicts.
    
    Args:
        resource_type: Resource type
        resource_id: Resource ID
    
    Returns:
        True if expired lock was deleted, False otherwise
    """
    try:
        existing = ResourceLock.objects.filter(
            resource_type=resource_type,
            resource_id=resource_id,
        ).first()
        
        if existing and existing.is_expired:
            logger.info(
                "SYS_CLAIM: Cleaning up expired lock",
                extra={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "lock_id": existing.id,
                    "expired_at": existing.expires_at.isoformat(),
                },
            )
            existing.delete()
            return True
        
        return False
        
    except Exception as e:
        logger.warning(
            "SYS_CLAIM: Expired lock cleanup failed (non-fatal)",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
        )
        return False


def sys_claim(payload: Dict[str, Any]) -> SyscallResult:
    """
    Kernel syscall: Claim a physical resource.
    
    This is the ONLY legal entry point from User Space for resource claiming.
    
    Guarantees:
    - Deterministic (same inputs → same outputs)
    - Physically safe (survives PostgreSQL UNIQUE constraint races)
    - ABI-compliant (uses kernel.abi classifiers)
    - Auditable (KernelAuditLog always exists)
    - Broken-transaction safe (no queries inside failed atomic blocks)
    - Re-entrant safe (same owner can re-claim)
    
    Payload (required):
        decision_id: str - Decision context ID
        context_hash: str - Request context hash (idempotency)
        resource_type: str - Type of resource (APPOINTMENT, etc.)
        resource_id: int|str - ID of resource to claim
        owner_id: int|str - ID of claiming owner (User PK)
        expires_at: datetime - Lock expiration (OR duration_seconds)
    
    Payload (optional):
        duration_seconds: int - Alternative to expires_at
        resource_key: str - Optional specificity key
    
    Returns:
        SyscallResult with audit_id, outcome dict, and outcome_code
    
    Behavior:
    1. Allocate audit root (always, even if crash)
    2. Idempotency CAS check
    3. Shadow pre-check (cleanup expired locks)
    4. Physical claim attempt (atomic)
    5. Handle conflicts (re-entrant detection)
    6. Update audit and return
    """
    # Step 0: Validate payload
    validation_error = _validate_payload(payload)
    if validation_error:
        # Fast-fail: create minimal audit and return rejection
        audit = _create_audit_root(payload)
        outcome = classify_failure(
            error_code="KERNEL/INVALID_PAYLOAD",
            internal_reason=validation_error,
        )
        _update_audit(audit, outcome)
        
        return SyscallResult(
            audit_id=str(audit.event_id),
            outcome=outcome.to_dict(),
            outcome_code=outcome.outcome_code,
        )
    
    # Extract payload fields
    decision_id = str(payload["decision_id"])
    context_hash = str(payload["context_hash"])
    resource_type = str(payload["resource_type"])
    resource_id = payload["resource_id"]  # Keep original type (int/str)
    owner_id = payload["owner_id"]  # Keep original type (int/str)
    resource_key = payload.get("resource_key")
    
    # Parse expires_at
    try:
        expires_at = _parse_expires_at(payload)
    except Exception as e:
        audit = _create_audit_root(payload)
        outcome = classify_failure(
            error_code="KERNEL/INVALID_PAYLOAD",
            internal_reason=f"Invalid expires_at/duration_seconds: {e}",
        )
        _update_audit(audit, outcome)
        
        return SyscallResult(
            audit_id=str(audit.event_id),
            outcome=outcome.to_dict(),
            outcome_code=outcome.outcome_code,
        )
    
    # Step 1: Allocate audit root (PID equivalent) FIRST
    audit = _create_audit_root(payload)
    
    try:
        # Step 2: Idempotency CAS
        idempotency_key = f"sys_claim:{decision_id}:{context_hash}"
        
        claimed, idempotency_record = claim_idempotency_key(
            idempotency_key=idempotency_key,
            event_type="SYS_CLAIM",
            decision_id=decision_id,
            context_hash=context_hash,
            event_id=str(audit.event_id),
        )
        
        if not claimed:
            # Idempotent replay detected
            logger.info(
                "SYS_CLAIM: Idempotent replay detected",
                extra={
                    "audit_id": str(audit.event_id),
                    "decision_id": decision_id,
                    "idempotency_key": idempotency_key,
                },
            )
            
            outcome = classify_success(
                claimed=False,
                message="Idempotent replay - operation already completed",
            )
            _update_audit(audit, outcome)
            
            return SyscallResult(
                audit_id=str(audit.event_id),
                outcome=outcome.to_dict(),
                outcome_code=outcome.outcome_code,
            )
        
        # Step 3: Shadow pre-check (cleanup expired locks)
        _cleanup_expired_lock(resource_type, resource_id)
        
        # Step 4 & 5: Physical claim with ZERO TOLERANCE broken transaction handling
        # ============================================================================
        # CRITICAL PATTERN:
        # - NO database access inside except IntegrityError
        # - Use flag to defer conflict vs re-entry check until AFTER atomic scope exits
        # - Only then (in finally or after try/except) do read-only query
        # ============================================================================
        
        final_outcome = None
        needs_post_atomic_check = False
        conflict_exception = None
        claimed_lock_id = None
        
        try:
            with transaction.atomic():
                lock = ResourceLock.objects.create(
                    decision_id=decision_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_key=resource_key,
                    owner_id=owner_id,
                    expires_at=expires_at,
                    status='active',
                )
                
                claimed_lock_id = lock.id
                
                logger.info(
                    "SYS_CLAIM: Lock claimed successfully",
                    extra={
                        "audit_id": str(audit.event_id),
                        "lock_id": lock.id,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "owner_id": owner_id,
                        "expires_at": expires_at.isoformat(),
                    },
                )
                
                # Success outcome (will be returned if atomic succeeds)
                final_outcome = classify_success(
                    claimed=True,
                    message="Resource lock claimed successfully",
                    lock_id=lock.id,
                )
        
        except IntegrityError as e:
            # 🚨 TRANSACTION IS BROKEN HERE
            # ABSOLUTELY NO DATABASE ACCESS
            # Set flag to check conflict vs re-entry AFTER atomic scope exits
            
            logger.warning(
                "SYS_CLAIM: Physical conflict detected (UNIQUE constraint)",
                extra={
                    "audit_id": str(audit.event_id),
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "owner_id": owner_id,
                    "error": str(e),
                },
            )
            
            needs_post_atomic_check = True
            conflict_exception = e
        
        finally:
            # ✅ SAFE ZONE: All atomic scopes have exited (or should have)
            # DAY-3 SAFETY FIX: Check if outer atomic block still active
            
            if needs_post_atomic_check:
                # TASK 1: Guard against outer transaction.atomic() decorator/caller
                if get_connection().in_atomic_block:
                    # 🚨 STILL IN ATOMIC BLOCK - Cannot safely query DB
                    # Return retryable failure instead of risking broken transaction
                    logger.error(
                        "SYS_CLAIM: Cannot perform post-conflict check (still in atomic block)",
                        extra={
                            "audit_id": str(audit.event_id),
                            "resource_type": resource_type,
                            "resource_id": resource_id,
                            "owner_id": owner_id,
                            "reason": "Outer transaction.atomic() prevents safe DB query",
                        },
                    )
                    
                    final_outcome = classify_failure(
                        error_code=KernelErrorCode.KERNEL_GENERIC_FAILURE,
                        internal_reason="Atomic context violation: cannot distinguish conflict vs re-entry",
                    )
                
                else:
                    # ✅ SAFE: No atomic block active - can query DB
                    
                    # TASK 2: Precise re-entry detection query
                    # Filter by FULL identity + ACTIVE locks only (not expired)
                    now = timezone.now()
                    existing = ResourceLock.objects.filter(
                        resource_type=resource_type,
                        resource_id=resource_id,
                        expires_at__gt=now,  # Only ACTIVE locks (not expired)
                        status='active',  # Only active status
                    ).order_by('-id').first()  # Deterministic ordering (newest first)
                    
                    # Re-entrant detection: Same owner already holds ACTIVE lock
                    if existing and str(existing.owner_id) == str(owner_id):
                        logger.info(
                            "SYS_CLAIM: Re-entrant claim detected (ownership guard)",
                            extra={
                                "audit_id": str(audit.event_id),
                                "resource_type": resource_type,
                                "resource_id": resource_id,
                                "owner_id": owner_id,
                                "existing_lock_id": existing.id,
                                "existing_decision_id": existing.decision_id,
                                "existing_expires_at": existing.expires_at.isoformat(),
                            },
                        )
                        
                        # V1 Kernel Design Decision:
                        # Re-entry is OK for idempotency but does NOT extend TTL
                        # to prevent stealth lease hijacking.
                        # Same owner can claim multiple times, but expires_at is unchanged.
                        
                        final_outcome = classify_success(
                            claimed=True,
                            message="Re-entrant claim detected - owner already holds lock",
                            existing_lock_id=existing.id,
                            existing_decision_id=existing.decision_id,
                        )
                    
                    else:
                        # Real contention: Different owner holds lock OR no active lock found
                        logger.warning(
                            "SYS_CLAIM: Real contention - different owner holds lock",
                            extra={
                                "audit_id": str(audit.event_id),
                                "resource_type": resource_type,
                                "resource_id": resource_id,
                                "requested_owner": owner_id,
                                "holding_owner": existing.owner_id if existing else None,
                                "holding_lock_id": existing.id if existing else None,
                            },
                        )
                        
                        final_outcome = classify_failure(
                            resource_conflict=True,
                            exception=conflict_exception,
                            internal_reason=f"Lock held by owner {existing.owner_id}" if existing else "Lock conflict",
                        )
            
            # TASK 3: SINGLE EXIT FUNNEL - Audit closure on ALL paths
            # Seal audit and return (best-effort, never blocks)
            if final_outcome:
                _update_audit(audit, final_outcome)
                
                return SyscallResult(
                    audit_id=str(audit.event_id),
                    outcome=final_outcome.to_dict(),
                    outcome_code=final_outcome.outcome_code,
                )
    
    except Exception as e:
        # Step 6: Unexpected error (generic failure)
        logger.error(
            "SYS_CLAIM: Unexpected error",
            extra={
                "audit_id": str(audit.event_id),
                "decision_id": decision_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "error": str(e),
            },
            exc_info=True,
        )
        
        outcome = classify_failure(
            exception=e,
            internal_reason=f"Unexpected syscall error: {e}",
        )
        _update_audit(audit, outcome)
        
        return SyscallResult(
            audit_id=str(audit.event_id),
            outcome=outcome.to_dict(),
            outcome_code=outcome.outcome_code,
        )

