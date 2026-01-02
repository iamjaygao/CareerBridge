"""Notification dispatch layer."""

from typing import Any, Dict, Optional

from signal_delivery.models import Notification
from signal_delivery.services.rules import (
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


def on_signal_created(signal_id: str) -> None:
    """
    Handle signal creation event.
    
    Called when a new ATS signal is created. For critical signals:
    - Creates a HumanReviewTask in human_loop
    - Notifies staff/admin via signal_delivery
    
    Args:
        signal_id: ID of the created signal
    """
    import logging
    from ats_signals.models import ATSSignal
    from human_loop.services.review_queue import create_review_task_for_signal
    from signal_delivery.services.rules import NotificationType
    
    logger = logging.getLogger(__name__)
    
    try:
        signal = ATSSignal.objects.get(id=signal_id)
        
        # If signal severity is 'critical', activate human loop
        if signal.severity == 'critical':
            logger.warning(
                f"Critical signal created: {signal_id} - activating human loop",
                extra={
                    'signal_id': signal_id,
                    'decision_slot_id': signal.decision_slot_id,
                    'signal_type': signal.signal_type,
                    'severity': signal.severity,
                    'category': signal.category,
                    'message': signal.message,
                }
            )
            
            # Create human review task
            try:
                review_task = create_review_task_for_signal(signal_id)
                
                if review_task:
                    # Notify staff/admin about critical signal requiring review
                    notify(
                        NotificationType.STAFF_CRITICAL_SIGNAL_REVIEW,
                        context={
                            'signal_id': str(signal.id),
                            'decision_slot_id': signal.decision_slot_id,
                            'review_task_id': str(review_task.id),
                        },
                        title=f"Critical Signal Requires Review",
                        message=(
                            f"Critical {signal.signal_type} signal detected: {signal.message}. "
                            f"Review task {review_task.id} created."
                        ),
                        priority='high',
                        payload={
                            'signal_id': str(signal.id),
                            'review_task_id': str(review_task.id),
                            'signal_type': signal.signal_type,
                            'category': signal.category,
                            'decision_slot_id': signal.decision_slot_id,
                        },
                    )
                    
                    logger.info(
                        f"Human loop activated for critical signal {signal_id}: review task {review_task.id} created",
                        extra={
                            'signal_id': signal_id,
                            'review_task_id': review_task.id,
                            'decision_slot_id': signal.decision_slot_id,
                        }
                    )
                else:
                    logger.warning(
                        f"Failed to create review task for critical signal {signal_id}",
                        extra={'signal_id': signal_id}
                    )
                    
            except Exception as task_error:
                # Log error but don't fail - signal is still created
                logger.error(
                    f"Failed to create review task for critical signal {signal_id}: {str(task_error)}",
                    exc_info=True,
                    extra={'signal_id': signal_id}
                )
        else:
            logger.debug(
                f"Signal created: {signal_id}",
                extra={
                    'signal_id': signal_id,
                    'decision_slot_id': signal.decision_slot_id,
                    'signal_type': signal.signal_type,
                    'severity': signal.severity,
                }
            )
            
    except ATSSignal.DoesNotExist:
        logger.error(f"Signal {signal_id} not found in on_signal_created handler")
    except Exception as e:
        logger.error(
            f"Error in on_signal_created handler for signal {signal_id}: {str(e)}",
            exc_info=True
        )
