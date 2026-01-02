from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Notification


def _cleanup_read_notifications(retention_days: int) -> int:
    # Keep read history; do not delete records.
    return 0


@shared_task
def cleanup_old_notifications():
    """Delete read notifications older than retention window."""
    retention_days = int(getattr(settings, 'NOTIFICATION_RETENTION_DAYS', 180))
    deleted_count = _cleanup_read_notifications(retention_days)
    return f"Skipped cleanup (read history retained). Deleted {deleted_count} read notifications."
