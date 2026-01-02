from django.core.management.base import BaseCommand

from signal_delivery.tasks import _cleanup_read_notifications
from django.conf import settings


class Command(BaseCommand):
    help = "Delete read notifications older than the retention window"

    def handle(self, *args, **options):
        retention_days = int(getattr(settings, 'NOTIFICATION_RETENTION_DAYS', 180))
        deleted_count = _cleanup_read_notifications(retention_days)
        self.stdout.write(
            self.style.SUCCESS(
                f"Skipped cleanup (read history retained). Deleted {deleted_count} read notifications."
            )
        )
