"""
Purge legacy TimeSlot records longer than 60 minutes with no active appointments.
"""

from django.core.management.base import BaseCommand
from django.db.models import F
from datetime import timedelta

from appointments.models import TimeSlot, Appointment


class Command(BaseCommand):
    help = "Delete legacy TimeSlot records longer than 60 minutes (no active appointments)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete records (default is dry-run).",
        )

    def handle(self, *args, **options):
        long_slots = TimeSlot.objects.filter(
            end_time__gt=F("start_time") + timedelta(minutes=60)
        )
        deletable = []
        for slot in long_slots:
            active_exists = Appointment.objects.filter(
                time_slot=slot,
                status__in=["pending", "confirmed"]
            ).exists()
            if not active_exists:
                deletable.append(slot.id)

        self.stdout.write(f"Legacy long slots found: {long_slots.count()}")
        self.stdout.write(f"Eligible for purge: {len(deletable)}")

        if not options["confirm"] or not deletable:
            return

        deleted = TimeSlot.objects.filter(id__in=deletable).delete()[0]
        self.stdout.write(f"Deleted {deleted} legacy time slots.")
