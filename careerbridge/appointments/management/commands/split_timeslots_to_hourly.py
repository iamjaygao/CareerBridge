"""
Split multi-hour TimeSlot records into 1-hour slots.
Skips slots that already have appointments.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import timedelta

from appointments.models import TimeSlot, Appointment


class Command(BaseCommand):
    help = "Split TimeSlot records longer than 60 minutes into hourly slots."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually perform the split (default is dry-run).",
        )

    def handle(self, *args, **options):
        long_slots = []
        for slot in TimeSlot.objects.all():
            duration = slot.end_time - slot.start_time
            if duration > timedelta(minutes=60):
                long_slots.append(slot)

        self.stdout.write(f"Found {len(long_slots)} slots longer than 60 minutes.")

        if not options["confirm"]:
            return

        for slot in long_slots:
            active_appointments = Appointment.objects.filter(
                time_slot=slot,
                status__in=["pending", "confirmed"]
            ).exists()
            if active_appointments or slot.reserved_appointment_id:
                self.stdout.write(
                    f"Skipping slot {slot.id} (has active appointments or reservation)."
                )
                continue
            has_any_appointments = Appointment.objects.filter(time_slot=slot).exists()

            with transaction.atomic():
                cursor = slot.start_time
                while cursor < slot.end_time:
                    next_end = cursor + timedelta(minutes=60)
                    TimeSlot.objects.create(
                        mentor=slot.mentor,
                        start_time=cursor,
                        end_time=next_end,
                        is_available=slot.is_available,
                        is_recurring=slot.is_recurring,
                        recurring_pattern=slot.recurring_pattern,
                        max_bookings=slot.max_bookings,
                        current_bookings=0,
                        price=slot.price,
                        currency=slot.currency,
                    )
                    cursor = next_end

                if has_any_appointments:
                    slot.is_available = False
                    slot.reserved_appointment = None
                    slot.reserved_until = None
                    slot.save(update_fields=[
                        "is_available",
                        "reserved_appointment",
                        "reserved_until",
                    ])
                else:
                    slot.delete()

        self.stdout.write("Split complete.")
