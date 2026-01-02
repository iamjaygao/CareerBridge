from celery import shared_task
from django.utils import timezone
from django.db.models import Count
import os

from payments.models import Payment
from decision_slots.models import Appointment
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from django.contrib.auth import get_user_model
from adminpanel.views import get_unified_system_health
from .models import DataExport
from .export_utils import build_export_rows, write_export_file


@shared_task
def notify_admin_payment_success_drop(drop_threshold: float = 0.2) -> int:
    """Notify admins when payment success rate drops sharply."""
    now = timezone.now()
    current_start = now - timezone.timedelta(days=1)
    prev_start = now - timezone.timedelta(days=2)

    def success_rate(start, end):
        total = Payment.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
            payment_type='appointment',
        ).count()
        if total == 0:
            return None
        success = Payment.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
            payment_type='appointment',
            status='completed',
        ).count()
        return success / total

    current_rate = success_rate(current_start, now)
    previous_rate = success_rate(prev_start, current_start)
    if current_rate is None or previous_rate is None:
        return 0
    if previous_rate - current_rate < drop_threshold:
        return 0

    admin_users = get_user_model().objects.filter(role='admin')
    notified = 0
    metric_key = 'payment_success_rate'
    for admin_user in admin_users:
        notify(
            NotificationType.ADMIN_PAYMENT_SUCCESS_DROP,
            context={
                'metric_key': metric_key,
                'admin': admin_user,
            },
            title='Payment success rate dropped',
            message=(
                f'Payment success rate dropped from {previous_rate:.1%} to {current_rate:.1%} '
                'in the last 24 hours.'
            ),
            priority='high',
            payload={'metric_key': metric_key},
        )
        notified += 1
    return notified


@shared_task
def notify_admin_metric_anomaly() -> int:
    """Notify admins when appointment volume is abnormal."""
    today = timezone.now().date()
    last_week_start = today - timezone.timedelta(days=7)

    daily_counts = (
        Appointment.objects.filter(scheduled_start__date__gte=last_week_start)
        .values('scheduled_start__date')
        .annotate(count=Count('id'))
    )
    counts = [item['count'] for item in daily_counts if item['scheduled_start__date'] != today]
    if not counts:
        return 0
    average = sum(counts) / len(counts)
    today_count = Appointment.objects.filter(scheduled_start__date=today).count()
    if average == 0:
        return 0
    deviation = abs(today_count - average) / average
    if deviation < 0.5:
        return 0

    admin_users = get_user_model().objects.filter(role='admin')
    notified = 0
    metric_key = 'appointments_today'
    for admin_user in admin_users:
        notify(
            NotificationType.ADMIN_METRIC_ANOMALY,
            context={
                'metric_key': metric_key,
                'admin': admin_user,
            },
            title='Appointment volume anomaly',
            message=(
                f'Today has {today_count} appointments vs weekly avg {average:.1f} '
                f'({deviation:.0%} deviation).'
            ),
            priority='normal',
            payload={'metric_key': metric_key},
        )
        notified += 1
    return notified


@shared_task
def notify_admin_risk_alerts() -> int:
    """Notify admins about users with repeated cancellations."""
    window_start = timezone.now() - timezone.timedelta(days=7)
    offenders = (
        Appointment.objects.filter(
            status='cancelled',
            updated_at__gte=window_start,
        )
        .values('user_id')
        .annotate(count=Count('id'))
        .filter(count__gte=3)
    )
    if not offenders:
        return 0

    User = get_user_model()
    admin_users = User.objects.filter(role='admin')
    notified = 0
    for offender in offenders:
        user = User.objects.filter(id=offender['user_id']).first()
        if not user:
            continue
        for admin_user in admin_users:
            notify(
                NotificationType.ADMIN_RISK_ALERT,
                context={
                    'user_id': user.id,
                    'admin': admin_user,
                },
                title='High cancellation activity',
                message=(
                    f'User {user.get_full_name() or user.username} has '
                    f'{offender["count"]} cancellations in the last 7 days.'
                ),
                priority='high',
                payload={'user_id': user.id},
            )
            notified += 1
    return notified


@shared_task
def notify_superadmin_system_alerts() -> int:
    """Notify superadmins when system health is degraded."""
    health = get_unified_system_health(use_cache=False)
    if health['system_health'] == 'healthy':
        return 0

    superadmins = get_user_model().objects.filter(role='superadmin')
    notified = 0
    incident_id = f"system_health_{health['system_health']}"
    for user in superadmins:
        notify(
            NotificationType.SUPERADMIN_SYSTEM_ALERT,
            context={
                'incident_id': incident_id,
                'superadmin': user,
            },
            title='System health degraded',
            message=(
                f"System health is {health['system_health']}. "
                f"DB: {health['database_status']}, Cache: {health['cache_status']}."
            ),
            priority='critical',
            payload={'incident_id': incident_id},
        )
        notified += 1
    return notified


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={'max_retries': 2})
def process_data_export(self, export_id):
    export = DataExport.objects.filter(id=export_id).first()
    if not export:
        return 0

    export.status = 'processing'
    export.started_at = timezone.now()
    export.save(update_fields=['status', 'started_at'])

    try:
        filters = export.filters or {}
        rows = build_export_rows(export.export_type, filters, export.date_from, export.date_to)
        file_path, file_size = write_export_file(export.export_type, rows, export.id)
        export.file_path = f"exports/{os.path.basename(file_path)}"
        export.file_size = file_size
        export.record_count = len(rows)
        export.status = 'completed'
        export.completed_at = timezone.now()
        export.save()
    except Exception as exc:
        export.status = 'failed'
        export.error_message = str(exc)
        export.completed_at = timezone.now()
        export.save()
        raise

    return export.id
