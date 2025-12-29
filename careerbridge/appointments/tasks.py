from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from .models import TimeSlot, Appointment
from notifications.services.dispatcher import notify
from notifications.services.rules import NotificationType


@shared_task
def release_expired_slot_holds():
    """
    Release expired slot holds and mark appointments as expired.
    Schedule this task to run every 1 minute via Celery Beat.
    """
    now = timezone.now()
    
    expired_slots = TimeSlot.objects.filter(
        is_available=False,
        reserved_until__lt=now,
        reserved_appointment__status='pending'
    ).select_related('reserved_appointment')
    
    for slot in expired_slots:
        with transaction.atomic():
            appointment = slot.reserved_appointment
            if appointment and appointment.status == 'pending':
                appointment.status = 'expired'
                appointment.save()
                
                # Notify student
                try:
                    appointment_details = appointment.get_notification_details()
                    notify(
                        NotificationType.APPOINTMENT_EXPIRED,
                        context={
                            'appointment_id': appointment.id,
                            'student': appointment.user,
                        },
                        title='Booking expired',
                        message=(
                            f'Your booking ({appointment_details}) with '
                            f'{appointment.mentor.user.get_full_name() or appointment.mentor.user.username} expired. '
                            'Please select a new time.'
                        ),
                        priority='high',
                        related_appointment=appointment,
                        payload=appointment.get_notification_payload(),
                    )
                except Exception:
                    pass
                
                slot.is_available = True
                slot.reserved_until = None
                slot.reserved_appointment = None
                booked_count = Appointment.objects.filter(
                    time_slot=slot,
                    status__in=['confirmed', 'completed']
                ).count()
                slot.current_bookings = booked_count
                slot.save()


@shared_task
def notify_staff_upcoming_appointments(hours_ahead: int = 24) -> int:
    """Notify staff about upcoming confirmed appointments."""
    now = timezone.now()
    cutoff = now + timezone.timedelta(hours=hours_ahead)
    appointments = Appointment.objects.filter(
        status='confirmed',
        scheduled_start__gte=now,
        scheduled_start__lte=cutoff,
    ).select_related('mentor__user', 'user')
    from django.contrib.auth import get_user_model

    staff_users = get_user_model().objects.filter(role='staff')
    if not staff_users.exists():
        return 0

    notified = 0
    for appointment in appointments:
        appointment_details = appointment.get_notification_details()
        for staff_user in staff_users:
            notify(
                NotificationType.STAFF_APPOINTMENT_UPCOMING,
                context={
                    'appointment_id': appointment.id,
                    'staff': staff_user,
                },
                title='Upcoming appointment',
                message=f'Upcoming appointment: {appointment_details}.',
                priority='normal',
                related_appointment=appointment,
                payload=appointment.get_notification_payload(),
            )
            notified += 1
    return notified


@shared_task
def notify_staff_unconfirmed_appointments(hours_old: int = 12, hours_until_start: int = 24) -> int:
    """Notify staff when mentors have not confirmed appointments in time."""
    now = timezone.now()
    created_cutoff = now - timezone.timedelta(hours=hours_old)
    start_cutoff = now + timezone.timedelta(hours=hours_until_start)
    appointments = Appointment.objects.filter(
        status='pending',
        created_at__lte=created_cutoff,
        scheduled_start__lte=start_cutoff,
    ).select_related('mentor__user', 'user')
    from django.contrib.auth import get_user_model

    staff_users = get_user_model().objects.filter(role='staff')
    if not staff_users.exists():
        return 0

    notified = 0
    for appointment in appointments:
        appointment_details = appointment.get_notification_details()
        for staff_user in staff_users:
            notify(
                NotificationType.STAFF_MENTOR_NO_CONFIRM,
                context={
                    'appointment_id': appointment.id,
                    'staff': staff_user,
                },
                title='Mentor confirmation overdue',
                message=f'Mentor has not confirmed appointment: {appointment_details}.',
                priority='high',
                related_appointment=appointment,
                payload=appointment.get_notification_payload(),
            )
            notified += 1
    return notified


@shared_task
def notify_staff_missing_mentor_feedback(hours_after: int = 48) -> int:
    """Notify staff when mentor feedback is missing after session completion."""
    cutoff = timezone.now() - timezone.timedelta(hours=hours_after)
    appointments = Appointment.objects.filter(
        status='completed',
        mentor_feedback='',
        updated_at__lte=cutoff,
    ).select_related('mentor__user', 'user')
    from django.contrib.auth import get_user_model

    staff_users = get_user_model().objects.filter(role='staff')
    if not staff_users.exists():
        return 0

    notified = 0
    for appointment in appointments:
        appointment_details = appointment.get_notification_details()
        for staff_user in staff_users:
            notify(
                NotificationType.STAFF_MENTOR_NO_FEEDBACK,
                context={
                    'appointment_id': appointment.id,
                    'staff': staff_user,
                },
                title='Mentor feedback missing',
                message=f'Mentor feedback missing for {appointment_details}.',
                priority='high',
                related_appointment=appointment,
                payload=appointment.get_notification_payload(),
            )
            notified += 1
    return notified


@shared_task
def notify_admin_slot_conflicts() -> int:
    """Notify admin when multiple appointments share the same mentor/time."""
    from django.contrib.auth import get_user_model

    conflicts = Appointment.objects.filter(
        status='confirmed'
    ).values('mentor_id', 'scheduled_start').annotate(count=Count('id')).filter(count__gt=1)

    admin_users = get_user_model().objects.filter(role='admin')
    if not admin_users.exists():
        return 0

    notified = 0
    for conflict in conflicts:
        mentor_id = conflict['mentor_id']
        scheduled_start = conflict['scheduled_start']
        metric_key = f"slot_conflict_{mentor_id}_{scheduled_start.isoformat()}"
        for admin_user in admin_users:
            notify(
                NotificationType.ADMIN_SLOT_CONFLICT,
                context={
                    'mentor_id': mentor_id,
                    'metric_key': metric_key,
                    'admin': admin_user,
                },
                title='Appointment slot conflict',
                message=(
                    f'Mentor {mentor_id} has {conflict["count"]} confirmed appointments at '
                    f'{scheduled_start}.'
                ),
                priority='high',
                payload={'mentor_id': mentor_id, 'metric_key': metric_key},
            )
            notified += 1
    return notified
