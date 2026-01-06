import logging
from typing import Any, Dict

from django.db import transaction

from appointments.models import Appointment
from gateai.kernel_events import (
    compute_context_hash,
    handle_kernel_failure,
    register_kernel_listener,
)
from kernel.models import KernelAuditLog
from payments.services import schedule_payout_for_appointment

logger = logging.getLogger(__name__)


def register_listeners() -> None:
    """Register payment listeners with the kernel."""
    register_kernel_listener("APPOINTMENT_COMPLETED", _handle_appointment_completed)


def _lock_boundary_from_appointment(appointment: Appointment) -> Any:
    """Return the OS-level time boundary used for context hashing."""
    if appointment.time_slot and appointment.time_slot.reserved_until:
        return appointment.time_slot.reserved_until
    return appointment.scheduled_end


def _handle_appointment_completed(event: Dict[str, Any]) -> None:
    """
    Kernel listener that executes payment-side effects for completed appointments.
    """
    event_id = event.get("event_id")
    idempotency_key = event.get("idempotency_key")
    context_hash = event.get("context_hash")
    payload = event.get("payload") or {}
    appointment_id = payload.get("appointment_id")

    if not appointment_id:
        handle_kernel_failure(event, "Missing appointment_id in kernel payload")
        return

    with transaction.atomic():
        try:
            audit_entry = KernelAuditLog.objects.select_for_update().get(event_id=event_id)
        except KernelAuditLog.DoesNotExist:
            # No audit row means kernel invariant already broken; record failure terminally.
            handle_kernel_failure(event, "Kernel audit row missing for event")
            return

        # Listener-level idempotency: drop if already handled
        if audit_entry.status == KernelAuditLog.STATUS_HANDLED:
            return

        prior_handled = KernelAuditLog.objects.filter(
            idempotency_key=idempotency_key,
            status=KernelAuditLog.STATUS_HANDLED,
        ).exclude(event_id=event_id)
        if prior_handled.exists():
            audit_entry.status = KernelAuditLog.STATUS_REJECTED
            audit_entry.failure_reason = "Idempotency replay"
            audit_entry.save(update_fields=["status", "failure_reason", "updated_at"])
            return

        try:
            appointment = Appointment.objects.select_for_update().get(id=appointment_id)
        except Appointment.DoesNotExist:
            audit_entry.status = KernelAuditLog.STATUS_FAILED
            audit_entry.failure_reason = "Appointment not found"
            audit_entry.save(update_fields=["status", "failure_reason", "updated_at"])
            handle_kernel_failure(event, "Appointment not found for payment listener")
            return

        expected_hash = compute_context_hash(
            appointment.id,
            appointment.user_id,
            event.get("event_type"),
            _lock_boundary_from_appointment(appointment),
        )
        if expected_hash != context_hash:
            audit_entry.status = KernelAuditLog.STATUS_FAILED
            audit_entry.failure_reason = "Context hash mismatch"
            audit_entry.save(update_fields=["status", "failure_reason", "updated_at"])
            handle_kernel_failure(event, "Context hash mismatch")
            return

        # Schedule payout bookkeeping (no external API calls here)
        schedule_payout_for_appointment(appointment)

        audit_entry.status = KernelAuditLog.STATUS_HANDLED
        audit_entry.failure_reason = ""
        audit_entry.save(update_fields=["status", "failure_reason", "updated_at"])

        logger.info(
            "Kernel payment listener handled event",
            extra={
                "event_id": event_id,
                "appointment_id": appointment_id,
                "idempotency_key": idempotency_key,
            },
        )

