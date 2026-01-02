"""
Delete legacy role-based business notifications.
Keeps system announcements intact.
"""

from django.core.management.base import BaseCommand

from signal_delivery.models import Notification
from signal_delivery.services.rules import BUSINESS_EVENTS, get_db_type


class Command(BaseCommand):
    help = "Purge role-based business notifications (target_role set)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete records (default is dry-run).",
        )

    def handle(self, *args, **options):
        business_types = {get_db_type(event) for event in BUSINESS_EVENTS}
        qs = Notification.objects.filter(
            target_role__isnull=False,
            notification_type__in=business_types,
        )

        total = qs.count()
        if not options["confirm"]:
            self.stdout.write(
                f"Dry-run: {total} role-based business notifications would be deleted."
            )
            return

        deleted = qs.delete()[0]
        self.stdout.write(f"Deleted {deleted} role-based business notifications.")
