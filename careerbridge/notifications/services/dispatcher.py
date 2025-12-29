"""Notification dispatch layer."""

from typing import Any, Dict, Optional

from notifications.models import Notification
from notifications.services.rules import (
    NotificationCategory,
    NotificationType,
    Role,
    get_db_type,
    get_notification_rule,
    is_business_event,
    is_system_event,
)


def _get_context_user(context: Dict[str, Any], role: Role):
    return context.get(role.value)


def _build_payload(context: Dict[str, Any], payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    combined = {}
    for key in (
        'appointment_id',
        'mentor_application_id',
        'resume_id',
        'payment_id',
        'support_ticket_id',
        'feedback_id',
        'report_id',
        'conversation_id',
        'metric_key',
        'incident_id',
        'change_id',
        'user_id',
        'mentor_id',
    ):
        if key in context:
            combined[key] = context[key]
    if payload:
        combined.update(payload)
    return combined


def _dedupe_exists(
    *,
    user,
    notification_type: str,
    dedupe_key: Optional[str],
    context: Dict[str, Any],
    related_appointment,
) -> bool:
    if not dedupe_key:
        return False
    if dedupe_key not in context:
        return False

    qs = Notification.objects.filter(user=user, notification_type=notification_type)

    if dedupe_key == 'appointment_id' and related_appointment is not None:
        qs = qs.filter(related_appointment=related_appointment)
    else:
        qs = qs.filter(**{f"payload__{dedupe_key}": context[dedupe_key]})

    return qs.exists()


def notify(
    event: NotificationType,
    *,
    context: Dict[str, Any],
    title: str,
    message: str,
    priority: str = 'normal',
    related_appointment=None,
    related_resume=None,
    related_mentor=None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    rule = get_notification_rule(event)
    db_type = get_db_type(event)
    combined_payload = _build_payload(context, payload)
    if related_appointment and hasattr(related_appointment, "get_notification_details"):
        combined_payload.setdefault(
            "appointment_details",
            related_appointment.get_notification_details(),
        )
        if getattr(related_appointment, "scheduled_start", None):
            combined_payload.setdefault(
                "scheduled_start",
                related_appointment.scheduled_start.isoformat(),
            )
        if getattr(related_appointment, "service", None):
            combined_payload.setdefault(
                "service_title",
                getattr(related_appointment.service, "title", None),
            )

    if is_system_event(event) and rule.category != NotificationCategory.SYSTEM:
        raise ValueError("System event must use SYSTEM category rules.")
    if is_business_event(event) and rule.category == NotificationCategory.SYSTEM:
        raise ValueError("Business event cannot use SYSTEM category rules.")

    if rule.category == NotificationCategory.SYSTEM:
        for role in rule.recipients:
            user = _get_context_user(context, role)
            if user is not None:
                raise ValueError("System notifications must not include user recipients.")
        for role in rule.recipients:
            Notification.objects.create(
                target_role=role.value,
                notification_type=db_type,
                title=title,
                message=message,
                priority=priority,
                related_appointment=related_appointment,
                related_resume=related_resume,
                related_mentor=related_mentor,
                payload=combined_payload,
            )
        return

    for role in rule.recipients:
        user = _get_context_user(context, role)
        if not user:
            raise ValueError("Business notifications require explicit user recipients.")

        if _dedupe_exists(
            user=user,
            notification_type=db_type,
            dedupe_key=rule.dedupe_key,
            context=context,
            related_appointment=related_appointment,
        ):
            continue

        Notification.objects.create(
            user=user,
            notification_type=db_type,
            title=title,
            message=message,
            priority=priority,
            related_appointment=related_appointment,
            related_resume=related_resume,
            related_mentor=related_mentor,
            payload=combined_payload,
        )
