"""
Identify role-based notifications that use business notification types.
This command is read-only and prints counts only.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from signal_delivery.models import Notification
from signal_delivery.services.rules import BUSINESS_EVENTS, get_db_type


class Command(BaseCommand):
    help = "Report role-based business notifications by role and type."

    def handle(self, *args, **options):
        business_types = {get_db_type(event) for event in BUSINESS_EVENTS}
        target_roles = ["admin", "staff", "superadmin"]

        qs = Notification.objects.filter(
            target_role__in=target_roles,
            notification_type__in=business_types,
        )

        total = qs.count()
        self.stdout.write(f"Total role-based business notifications: {total}")

        breakdown = (
            qs.values("target_role", "notification_type")
            .annotate(count=Count("id"))
            .order_by("target_role", "notification_type")
        )

        for item in breakdown:
            self.stdout.write(
                f"{item['target_role']}: {item['notification_type']} = {item['count']}"
            )
