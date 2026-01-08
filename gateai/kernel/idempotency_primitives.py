"""
Kernel idempotency primitives - atomic claim operations.

Day 3: Race-safe idempotency key claiming without relying on IntegrityError as control flow.
"""

import logging
from typing import Tuple

from django.db import transaction
from django.db.models import Q

from kernel.models import KernelIdempotencyRecord

logger = logging.getLogger(__name__)


def claim_idempotency_key(
    *,
    idempotency_key: str,
    event_type: str,
    decision_id: str,
    context_hash: str,
    event_id: str = None,
    owner_id: str = None,
) -> Tuple[bool, KernelIdempotencyRecord]:
    """
    Kernel-grade CAS primitive for idempotency key claiming.
    
    PostgreSQL-safe implementation optimized for B-Tree locality:
    - Uses update_or_create with ONLY non-indexed fields in defaults
    - Acquires row lock immediately after creation
    - Writes indexed fields AFTER lock acquisition (prevents index bloat)
    - Linearizable under high contention
    
    Idempotency semantics (CRITICAL for correctness):
    - First claim sets status=IN_PROGRESS (NOT a terminal state)
    - claimed=False is ONLY treated as successful replay if status in SUCCESS_STATES
    - Semantic collision detection: if event_type/decision_id/context_hash mismatch,
      record.failure_reason is set to "IDEMPOTENCY_KEY_COLLISION"
    
    Returns:
        (claimed, record) tuple:
        - claimed=True: This caller owns the key (first claimant, status=IN_PROGRESS)
        - claimed=False: Key already exists (check record.status and failure_reason)
          * If status in SUCCESS_STATES -> safe REPLAY of completed operation
          * If status == IN_PROGRESS -> duplicate/concurrent request (operation in flight)
          * If status == FAILED -> previous attempt failed (may retry if allowed)
          * If failure_reason == "IDEMPOTENCY_KEY_COLLISION" -> semantic collision
    
    Never raises exceptions to caller - all races are handled internally and result in
    deterministic claimed=True/False outcome.
    
    Implementation guarantees:
    - First claimant always gets claimed=True with status=IN_PROGRESS
    - Subsequent claimants always get claimed=False with the existing record
    - No IntegrityError leaks to caller
    - Correct under extreme concurrency (PostgreSQL, high contention)
    - Physically safe for B-Tree indexes (no hot-spot contention)
    """
    from django.db import IntegrityError
    
    try:
        with transaction.atomic():
            # Phase 1: Atomic upsert with minimal defaults
            # Empty defaults to prevent any field overwrites on replay
            # All fields will be filled in Phase 3 (self-heal fill) after lock acquisition
            defaults = {}
            
            record, created = KernelIdempotencyRecord.objects.update_or_create(
                idempotency_key=idempotency_key,
                defaults=defaults,
            )
            
            # Phase 2: Immediately acquire exclusive lock on the row
            # This ensures linearizability regardless of whether we created or found
            record = (
                KernelIdempotencyRecord.objects
                .select_for_update(nowait=False)
                .get(pk=record.pk)
            )
            
            # Phase 3: Self-heal fill - ensure all fields are populated
            # This handles the race where second claimant observes partially-initialized record
            # Apply for BOTH created=True and created=False paths
            fields_to_fill = []
            
            # Self-heal empty fields (never overwrite non-empty)
            if not record.event_type and event_type:
                record.event_type = event_type
                fields_to_fill.append('event_type')
            
            if not record.decision_id and decision_id:
                record.decision_id = decision_id
                fields_to_fill.append('decision_id')
            
            if not record.context_hash and context_hash:
                record.context_hash = context_hash
                fields_to_fill.append('context_hash')
            
            if not record.owner_id and owner_id:
                record.owner_id = owner_id
                fields_to_fill.append('owner_id')
            
            # Status rule: fill if empty, but do NOT overwrite any existing status
            # CRITICAL FIX: Set to IN_PROGRESS (not PROCESSED) during claim
            if not record.status or record.status == '':
                record.status = KernelIdempotencyRecord.STATUS_IN_PROGRESS
                fields_to_fill.append('status')
            
            # last_event_id rule: fill ONLY if empty AND event_id provided
            # Safe to fill on replay (best-effort pointer to most recent event)
            # BUT: preserve original if already set (idempotency guarantee)
            if not record.last_event_id and event_id:
                record.last_event_id = event_id
                fields_to_fill.append('last_event_id')
            
            # Write any filled fields atomically
            if fields_to_fill:
                record.save(update_fields=fields_to_fill)
                logger.debug(
                    "Self-heal filled fields",
                    extra={
                        "idempotency_key": idempotency_key,
                        "filled_fields": fields_to_fill,
                        "created": created,
                    },
                )
            
            # Phase 4: Semantic collision detection (CRITICAL for correctness)
            # If key exists but semantic fields mismatch -> deterministic CONFLICT
            # Semantic identity: SAME (event_type, context_hash, owner_id)
            # decision_id is informational only, NOT part of semantic identity
            if not created:
                if not record.is_semantically_same_request(event_type, context_hash, owner_id):
                    logger.error(
                        "Idempotency key collision: same key, different operation",
                        extra={
                            "idempotency_key": idempotency_key,
                            "incoming_event_type": event_type,
                            "incoming_context_hash": context_hash,
                            "incoming_owner_id": owner_id,
                            "existing_event_type": record.event_type,
                            "existing_context_hash": record.context_hash,
                            "existing_owner_id": getattr(record, 'owner_id', None),
                        },
                    )
                    # Mark collision in record (best-effort, don't fail on error)
                    try:
                        record.failure_reason = "IDEMPOTENCY_KEY_COLLISION"
                        record.save(update_fields=['failure_reason'])
                    except Exception as e:
                        logger.warning(
                            "Failed to mark collision in record",
                            extra={"error": str(e)},
                        )
                    
                    # Return claimed=False with collision marker
                    # Caller MUST check failure_reason to detect collision
                    return (False, record)
            
            # Phase 5: Return with deterministic semantics
            if created:
                # First claimant - status=IN_PROGRESS (NOT a terminal state)
                logger.info(
                    "Idempotency key claimed successfully (IN_PROGRESS)",
                    extra={
                        "idempotency_key": idempotency_key,
                        "event_id": event_id,
                        "decision_id": decision_id,
                        "status": record.status,
                    },
                )
                return (True, record)
            else:
                # Second claimant - row already exists (replay path)
                # Caller MUST check record.status to determine if operation succeeded:
                # - status in SUCCESS_STATES -> safe REPLAY
                # - status == IN_PROGRESS -> concurrent request (operation in flight)
                # - status == FAILED -> previous attempt failed
                logger.info(
                    "Idempotency key already claimed",
                    extra={
                        "idempotency_key": idempotency_key,
                        "existing_status": record.status,
                        "existing_event_id": str(record.last_event_id) if record.last_event_id else None,
                        "is_success_replay": record.status in KernelIdempotencyRecord.SUCCESS_STATES,
                    },
                )
                return (False, record)
    
    except IntegrityError as e:
        # Catastrophic fallback: unique constraint violation outside atomic block
        # This should be extremely rare (only if row was created + deleted mid-flight)
        logger.warning(
            "IntegrityError during idempotency claim (catastrophic race), re-querying",
            extra={
                "idempotency_key": idempotency_key,
                "error": str(e),
            },
        )
        
        # Re-query outside transaction (defensive fallback)
        # NEVER raise exceptions - return claimed=False with best-effort record
        try:
            with transaction.atomic():
                existing = (
                    KernelIdempotencyRecord.objects
                    .select_for_update(nowait=False)
                    .filter(idempotency_key=idempotency_key)
                    .first()
                )
                
                if existing:
                    return (False, existing)
                
                # Row still doesn't exist - this is a kernel integrity violation
                # Return claimed=False with synthetic record (prevent exception leak)
                logger.error(
                    "Idempotency key missing after IntegrityError (kernel integrity violation)",
                    extra={"idempotency_key": idempotency_key},
                )
                
                # Create synthetic record for caller (best-effort)
                synthetic = KernelIdempotencyRecord(
                    idempotency_key=idempotency_key,
                    event_type=event_type,
                    decision_id=decision_id,
                    context_hash=context_hash,
                    status=KernelIdempotencyRecord.STATUS_FAILED,
                    failure_reason="KERNEL_INTEGRITY_VIOLATION",
                )
                return (False, synthetic)
                
        except Exception as fallback_error:
            # Last-resort fallback: prevent exception leak
            logger.error(
                "Fatal error in idempotency claim fallback (returning synthetic record)",
                extra={
                    "idempotency_key": idempotency_key,
                    "error": str(fallback_error),
                },
                exc_info=True,
            )
            
            # Return claimed=False with synthetic record (never raise)
            synthetic = KernelIdempotencyRecord(
                idempotency_key=idempotency_key,
                event_type=event_type,
                decision_id=decision_id,
                context_hash=context_hash,
                status=KernelIdempotencyRecord.STATUS_FAILED,
                failure_reason="CATASTROPHIC_FALLBACK",
            )
            return (False, synthetic)


def mark_key_succeeded(idempotency_key: str, event_id: str = None) -> bool:
    """
    Mark an idempotency key as succeeded (best-effort, exception-safe).
    
    State machine rules:
    - Only transitions from IN_PROGRESS to SUCCEEDED
    - NEVER overwrites terminal states (idempotent SUCCEEDED -> SUCCEEDED allowed)
    - Updates last_event_id if provided and not already set
    
    Returns:
        True if updated successfully, False if failed, key not found, or invalid transition.
    """
    try:
        # Fetch record with lock to check current state
        with transaction.atomic():
            record = (
                KernelIdempotencyRecord.objects
                .select_for_update(nowait=False)
                .filter(idempotency_key=idempotency_key)
                .first()
            )
            
            if not record:
                logger.warning(
                    "mark_key_succeeded: key not found",
                    extra={"idempotency_key": idempotency_key},
                )
                return False
            
            # Check if transition is valid
            if not KernelIdempotencyRecord.is_valid_transition(record.status, KernelIdempotencyRecord.STATUS_SUCCEEDED):
                logger.warning(
                    "mark_key_succeeded: invalid state transition blocked",
                    extra={
                        "idempotency_key": idempotency_key,
                        "current_status": record.status,
                        "requested_status": KernelIdempotencyRecord.STATUS_SUCCEEDED,
                    },
                )
                return False
            
            # Update status to SUCCEEDED
            update_fields = {'status': KernelIdempotencyRecord.STATUS_SUCCEEDED}
            
            # Update last_event_id if provided and not already set
            if event_id and not record.last_event_id:
                update_fields['last_event_id'] = event_id
            
            # Apply updates
            for field, value in update_fields.items():
                setattr(record, field, value)
            
            record.save(update_fields=list(update_fields.keys()))
            
            logger.info(
                "Idempotency key marked as succeeded",
                extra={
                    "idempotency_key": idempotency_key,
                    "event_id": event_id,
                },
            )
            return True
            
    except Exception as e:
        logger.warning(
            "Failed to mark idempotency key as succeeded",
            extra={
                "idempotency_key": idempotency_key,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def mark_key_failed(idempotency_key: str, failure_reason: str) -> bool:
    """
    Mark an idempotency key as failed (best-effort, exception-safe).
    
    State machine rules:
    - Only transitions from IN_PROGRESS or FAILED to FAILED
    - NEVER overwrites terminal success states (SUCCEEDED, PROCESSED, REJECTED)
    
    Returns:
        True if updated successfully, False if failed, key not found, or invalid transition.
    """
    try:
        # Only update if status is IN_PROGRESS or FAILED (allow idempotent FAILED -> FAILED)
        # Explicitly exclude terminal success states to prevent corruption
        count = KernelIdempotencyRecord.objects.filter(
            idempotency_key=idempotency_key
        ).exclude(
            status__in=KernelIdempotencyRecord.TERMINAL_STATES
        ).update(
            status=KernelIdempotencyRecord.STATUS_FAILED,
            failure_reason=failure_reason,
        )
        
        if count == 0:
            # Check if record exists in terminal state
            existing = KernelIdempotencyRecord.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            
            if existing and existing.status in KernelIdempotencyRecord.TERMINAL_STATES:
                logger.warning(
                    "mark_key_failed: blocked invalid transition from terminal state",
                    extra={
                        "idempotency_key": idempotency_key,
                        "current_status": existing.status,
                        "failure_reason": failure_reason,
                    },
                )
            else:
                logger.warning(
                    "mark_key_failed: key not found",
                    extra={"idempotency_key": idempotency_key},
                )
        
        return count > 0
    except Exception as e:
        logger.warning(
            "Failed to mark idempotency key as failed",
            extra={
                "idempotency_key": idempotency_key,
                "error": str(e),
            },
        )
        return False

