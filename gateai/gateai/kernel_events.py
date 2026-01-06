"""
GateAI OS Kernel Event System

Day 2: Deterministic kernel event ABI with audit and listener dispatch.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from kernel.models import KernelAuditLog
from kernel.abi import (
    KernelOutcome,
    KernelOutcomeCode,
    KernelErrorCode,
    classify_failure,
    classify_success,
    map_outcome_to_status,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
FAILURE_EVENT_TYPE = "KERNEL_DECISION_FAILED"
_LISTENERS: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
_RESOURCE_RELEASE_CALLBACK: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None


class ErrorCode:
    """
    DEPRECATED: Use kernel.abi.KernelErrorCode instead.
    
    Maintained for backward compatibility with Step 2 code.
    All values are aliases to namespaced KernelErrorCode constants.
    """
    LISTENER_EXCEPTION = KernelErrorCode.KERNEL_LISTENER_EXCEPTION
    CONTEXT_HASH_MISMATCH = KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH
    IDEMPOTENCY_VIOLATION = KernelErrorCode.KERNEL_IDEMPOTENCY_VIOLATION
    INVALID_PAYLOAD = KernelErrorCode.KERNEL_INVALID_PAYLOAD
    PAYMENT_EXECUTION_ERROR = KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE  # Generic now
    RESOURCE_LOCK_EXPIRED = KernelErrorCode.KERNEL_RESOURCE_LOCK_EXPIRED
    GENERIC_FAILURE = KernelErrorCode.KERNEL_GENERIC_FAILURE


def register_kernel_listener(event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Register a listener for a kernel event type."""
    if not event_type or not handler:
        return
    _LISTENERS.setdefault(event_type, [])
    if handler not in _LISTENERS[event_type]:
        _LISTENERS[event_type].append(handler)


def register_resource_release_callback(callback: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
    """
    Register callback for releasing resources on kernel failure.
    
    Callback receives payload dict and returns result dict with keys:
    - success: bool
    - released_count: int (number of locks released)
    - error: str (if success=False)
    
    Thread-safe: module-level variable assignment is atomic in Python.
    """
    global _RESOURCE_RELEASE_CALLBACK
    _RESOURCE_RELEASE_CALLBACK = callback


def get_resource_release_callback() -> Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]:
    """Get the registered resource release callback, if any."""
    return _RESOURCE_RELEASE_CALLBACK


def compute_context_hash(
    resource_id: Any, owner_id: Any, action_type: str, lock_expires_at: Optional[Any]
) -> str:
    """Compute deterministic SHA256 hash binding resource + boundary."""
    expires_norm = ""
    if isinstance(lock_expires_at, datetime):
        expires_norm = lock_expires_at.astimezone(timezone.utc).isoformat()
    elif lock_expires_at:
        expires_norm = str(lock_expires_at)
    base = f"{resource_id}|{owner_id}|{action_type}|{expires_norm}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def compute_idempotency_key(event_type: str, decision_id: Any, context_hash: str) -> str:
    """Compute deterministic idempotency key from immutable event facts."""
    base = f"{event_type}|{decision_id}|{context_hash}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _ensure_flat_payload(payload: dict) -> None:
    """Ensure payload is flat JSON (no nested dict/list)."""
    for value in payload.values():
        if isinstance(value, (dict, list)):
            raise ValueError("Kernel payload must be flat JSON (no nested objects)")


def emit_kernel_event(event_type: str, payload: dict) -> uuid.UUID:
    """
    Emit OS-level kernel event with deterministic, auditable envelope.

    Persist audit log first, then dispatch to listeners after commit.
    """
    if not event_type:
        raise ValueError("event_type is required")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")

    _ensure_flat_payload(payload)

    decision_id = payload.get("decision_id")
    resource_id = payload.get("resource_id")
    owner_id = payload.get("owner_id")
    action_type = payload.get("action_type") or event_type
    lock_expires_at = payload.get("lock_expires_at")

    if decision_id is None or resource_id is None or owner_id is None:
        raise ValueError("decision_id, resource_id, and owner_id are required for kernel emission")

    context_hash = payload.get("context_hash") or compute_context_hash(
        resource_id, owner_id, action_type, lock_expires_at
    )
    idempotency_key = payload.get("idempotency_key") or compute_idempotency_key(
        event_type, decision_id, context_hash
    )
    if not idempotency_key:
        raise ValueError("idempotency_key is required and must be deterministic")

    emitted_at = timezone.now()
    audit_entry = KernelAuditLog.objects.create(
        event_type=event_type,
        decision_id=str(decision_id),
        idempotency_key=idempotency_key,
        context_hash=context_hash,
        schema_version=SCHEMA_VERSION,
        payload={
            **payload,
            "context_hash": context_hash,
            "idempotency_key": idempotency_key,
            "schema_version": SCHEMA_VERSION,
            "emitted_at": emitted_at.isoformat(),
        },
        status=KernelAuditLog.STATUS_EMITTED,
    )

    event_data = {
        "event_id": str(audit_entry.event_id),
        "event_type": event_type,
        "decision_id": str(decision_id),
        "idempotency_key": idempotency_key,
        "context_hash": context_hash,
        "schema_version": SCHEMA_VERSION,
        "emitted_at": emitted_at.isoformat(),
        "payload": {**payload},
    }

    logger.info(
        "[KERNEL EVENT EMITTED]",
        extra={
            "event_type": event_type,
            "decision_id": decision_id,
            "idempotency_key": idempotency_key,
            "context_hash": context_hash,
            "event_id": str(audit_entry.event_id),
            "schema_version": SCHEMA_VERSION,
        },
    )
    
    # Store ABI outcome for successful emission
    outcome = classify_success(claimed=True, message=f"Event {event_type} emitted")
    KernelAuditLog.store_outcome(audit_entry.event_id, outcome)

    def _dispatch() -> None:
        handlers = _LISTENERS.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Kernel listener failed", extra={"event_id": str(audit_entry.event_id)})
                _handle_failure_event(event_data, str(exc))

    transaction.on_commit(_dispatch)
    return audit_entry.event_id


def _handle_failure_event(event_data: Dict[str, Any], reason: str) -> None:
    """
    Terminal failure handler: log failure + release locks atomically.
    
    Classifies failure into ABI outcome and stores in audit log.
    """
    if event_data.get("event_type") == FAILURE_EVENT_TYPE:
        return
    
    # Classify failure (generic listener exception)
    outcome = classify_failure(
        exception=None,
        internal_reason=reason,
    )

    with transaction.atomic():
        event_id = event_data.get("event_id")
        
        # Update original event with failure status
        KernelAuditLog.objects.filter(event_id=event_id).update(
            status=map_outcome_to_status(outcome),
            failure_reason=reason
        )
        
        # Store outcome in original event
        KernelAuditLog.store_outcome(event_id, outcome)
        
        # Create KERNEL_DECISION_FAILED event
        failure_idempotency = compute_idempotency_key(
            FAILURE_EVENT_TYPE, event_data.get("decision_id"), event_data.get("context_hash", "")
        )
        KernelAuditLog.objects.create(
            event_type=FAILURE_EVENT_TYPE,
            decision_id=str(event_data.get("decision_id")),
            idempotency_key=failure_idempotency,
            context_hash=event_data.get("context_hash", ""),
            schema_version=SCHEMA_VERSION,
            payload={
                "source_event_id": event_data.get("event_id"),
                "source_event_type": event_data.get("event_type"),
                "reason": reason,
            },
            status=KernelAuditLog.STATUS_FAILED,
            failure_reason=reason,
        )

        _release_resource_lock(event_data.get("payload", {}), reason)


def handle_kernel_failure(event_data: Dict[str, Any], reason: str) -> None:
    """Public wrapper for failure handling (terminal, no re-emission)."""
    _handle_failure_event(event_data, reason)


def _release_resource_lock(payload: Dict[str, Any], reason: str) -> None:
    """
    Release ResourceLock via registered callback (exception-safe).
    
    Classifies callback outcomes and logs appropriately.
    Never raises - swallows exceptions to prevent kernel poisoning.
    """
    callback = get_resource_release_callback()
    
    if callback is None:
        logger.warning(
            "No resource release callback registered; skipping lock release",
            extra={"reason": reason, "payload_keys": list(payload.keys())},
        )
        return
    
    try:
        result = callback(payload)
        
        if result.get("success"):
            logger.info(
                "Resource locks released via callback",
                extra={
                    "released_count": result.get("released_count", 0),
                    "reason": reason,
                },
            )
        else:
            # Callback reported failure
            outcome = classify_failure(
                callback_failure=True,
                internal_reason=result.get("error", "unknown"),
            )
            logger.warning(
                "Resource release callback reported failure",
                extra={
                    "error": result.get("error", "unknown"),
                    "reason": reason,
                    "outcome": outcome.to_dict(),
                },
            )
    
    except Exception as e:
        # Callback raised exception
        outcome = classify_failure(
            exception=e,
            callback_failure=True,
        )
        logger.error(
            "Resource release callback raised exception (swallowed)",
            extra={
                "error": str(e),
                "reason": reason,
                "outcome": outcome.to_dict(),
            },
            exc_info=True,
        )
