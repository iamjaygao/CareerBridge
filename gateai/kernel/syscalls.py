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

from django.db import connection, transaction, IntegrityError
from django.utils import timezone

from kernel.abi import classify_success, classify_failure, map_outcome_to_status, KernelOutcome, KernelErrorCode
from kernel.idempotency_primitives import claim_idempotency_key
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
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


def _delete_expired_active_lock(resource_type: str, resource_id: Any, now: datetime) -> int:
    """
    Remove an expired ACTIVE lock on this resource, in the caller's transaction.

    A single conditional DELETE (no read-then-write): under READ COMMITTED a
    concurrent deleter blocks on the row lock, re-checks the WHERE clause and
    deletes nothing. Correctness does not depend on the count; the partial
    unique index decides who gets the resource.
    """
    table = ResourceLock._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {table} WHERE resource_type = %s AND resource_id = %s "
            f"AND status = 'active' AND expires_at <= %s",
            [resource_type, resource_id, now],
        )
        return cursor.rowcount


# KERNEL INVARIANT:
# ----------------
# Arbitration MUST occur at most once per (resource_type, resource_id, context_hash).
#
# Once a winning idempotency record is written:
#   - The decision is FINAL.
#   - All subsequent sys_claim calls MUST short-circuit via idempotency replay.
#   - No re-arbitration, no fairness re-evaluation, no retries.
#
# Any arbitration exception is treated as a deterministic terminal loss,
# NOT a transient failure. This syscall is deliberately FAIL-CLOSED.
#
# Rationale:
#   - Prevent arbitration storms
#   - Prevent retry amplification
#   - Preserve deterministic, auditable outcomes

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
    
    try:
        owner_pk = int(owner_id)
    except (TypeError, ValueError):
        audit = _create_audit_root(payload)
        outcome = classify_failure(
            error_code="KERNEL/INVALID_PAYLOAD",
            internal_reason=f"owner_id must be an integer user id, got {owner_id!r}",
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
        # One transaction for idempotency + physical claim + final status.
        # If the caller already has a transaction this is a savepoint, so a
        # failure here never poisons the caller's transaction.
        with transaction.atomic():
            outcome = _claim_in_transaction(
                audit=audit,
                decision_id=decision_id,
                context_hash=context_hash,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_key=resource_key,
                owner_pk=owner_pk,
                expires_at=expires_at,
            )
    except Exception as e:
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


def _set_idempotency_status(record: KernelIdempotencyRecord, status: str) -> None:
    record.status = status
    record.save(update_fields=["status"])


def _claim_in_transaction(
    *,
    audit: KernelAuditLog,
    decision_id: str,
    context_hash: str,
    resource_type: str,
    resource_id: Any,
    resource_key: Optional[str],
    owner_pk: int,
    expires_at: datetime,
) -> KernelOutcome:
    """
    Idempotency + physical claim. Must run inside transaction.atomic().

    Idempotency (key = decision_id + context_hash), with the record row-locked
    for the rest of the transaction so same-key requests are serialised:
    - key held by a different owner          -> CONFLICT (refused)
    - key already SUCCEEDED (same owner)     -> REPLAY
    - key already REJECTED (a lost claim)    -> CONFLICT
    - otherwise                              -> attempt the claim

    Physical claim, relying only on database mechanisms:
    - expired active lock removed by a conditional DELETE
    - INSERT inside a savepoint; the partial unique index
      (one active lock per resource) arbitrates concurrent inserts
    - on IntegrityError the savepoint is rolled back and the holder is read
      with SELECT ... FOR UPDATE: same owner -> re-entrant OK, else CONFLICT
    """
    idempotency_key = f"sys_claim:{decision_id}:{context_hash}"
    owner = str(owner_pk)

    existing_record = (
        KernelIdempotencyRecord.objects.select_for_update()
        .filter(idempotency_key=idempotency_key)
        .first()
    )
    if existing_record and existing_record.owner_id and existing_record.owner_id != owner:
        logger.warning(
            "SYS_CLAIM: Idempotency key presented by a different owner",
            extra={"audit_id": str(audit.event_id), "idempotency_key": idempotency_key},
        )
        return classify_failure(
            resource_conflict=True,
            internal_reason="Idempotency key belongs to a different owner",
        )

    claimed, record = claim_idempotency_key(
        idempotency_key=idempotency_key,
        event_type="SYS_CLAIM",
        decision_id=decision_id,
        context_hash=context_hash,
        event_id=str(audit.event_id),
        owner_id=owner,
    )
    if record.pk is None:
        # Synthetic record: the primitive could not read or create the key.
        return classify_failure(
            error_code=KernelErrorCode.KERNEL_GENERIC_FAILURE,
            internal_reason=f"Idempotency claim failed: {record.failure_reason}",
        )

    now = timezone.now()

    if not claimed:
        if record.status in KernelIdempotencyRecord.SUCCESS_STATES:
            held = ResourceLock.objects.filter(
                resource_type=resource_type, resource_id=resource_id,
                status="active", owner_id=owner_pk, expires_at__gt=now,
            ).first()
            logger.info(
                "SYS_CLAIM: Idempotent replay detected",
                extra={"audit_id": str(audit.event_id), "idempotency_key": idempotency_key},
            )
            return classify_success(
                claimed=False,
                message="Idempotent replay - operation already completed",
                lock_id=held.id if held else None,
                lock_active=held is not None,
            )
        if record.status == KernelIdempotencyRecord.STATUS_REJECTED:
            return classify_failure(
                resource_conflict=True,
                internal_reason="Idempotent replay of a claim that lost the resource",
            )
        # IN_PROGRESS (left by an interrupted attempt) or FAILED: we hold the
        # record's row lock, so it is safe to attempt the claim now.

    _delete_expired_active_lock(resource_type, resource_id, now)

    try:
        with transaction.atomic():  # savepoint: an IntegrityError rolls back only this
            lock = ResourceLock.objects.create(
                decision_id=decision_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_key=resource_key,
                owner_id=owner_pk,
                expires_at=expires_at,
                status="active",
            )
    except IntegrityError as e:
        holder = (
            ResourceLock.objects.select_for_update()
            .filter(resource_type=resource_type, resource_id=resource_id, status="active")
            .first()
        )
        if holder and holder.owner_id == owner_pk and holder.expires_at > now:
            # Re-entry is OK but does NOT extend the TTL (no stealth lease extension).
            logger.info(
                "SYS_CLAIM: Re-entrant claim detected (ownership guard)",
                extra={"audit_id": str(audit.event_id), "existing_lock_id": holder.id},
            )
            _set_idempotency_status(record, KernelIdempotencyRecord.STATUS_SUCCEEDED)
            return classify_success(
                claimed=True,
                message="Re-entrant claim detected - owner already holds lock",
                lock_id=holder.id,
                existing_lock_id=holder.id,
                existing_decision_id=holder.decision_id,
            )

        logger.warning(
            "SYS_CLAIM: Real contention - resource held by another owner",
            extra={
                "audit_id": str(audit.event_id),
                "resource_type": resource_type,
                "resource_id": resource_id,
                "requested_owner": owner_pk,
                "holding_owner": holder.owner_id if holder else None,
            },
        )
        _set_idempotency_status(record, KernelIdempotencyRecord.STATUS_REJECTED)
        return classify_failure(
            resource_conflict=True,
            exception=e,
            internal_reason=f"Lock held by owner {holder.owner_id}" if holder else "Lock conflict",
        )

    logger.info(
        "SYS_CLAIM: Lock claimed successfully",
        extra={
            "audit_id": str(audit.event_id),
            "lock_id": lock.id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "owner_id": owner_pk,
            "expires_at": expires_at.isoformat(),
        },
    )
    _set_idempotency_status(record, KernelIdempotencyRecord.STATUS_SUCCEEDED)
    return classify_success(
        claimed=True,
        message="Resource lock claimed successfully",
        lock_id=lock.id,
    )
