from django.core.management.base import BaseCommand

from decision_slots.models import Appointment


class Command(BaseCommand):
    help = "Backfill appointment titles to use service titles when available."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )
        parser.add_argument(
            "--mentor-id",
            type=int,
            default=None,
            help="Only backfill appointments for a specific mentor ID.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        mentor_id = options["mentor_id"]

        appointments = Appointment.objects.select_related("service")
        if mentor_id:
            appointments = appointments.filter(mentor_id=mentor_id)

        updated = 0
        for appointment in appointments:
            if not appointment.service or not appointment.service.title:
                continue
            if appointment.title and not appointment.title.lower().startswith("session with"):
                continue
            if not appointment.title:
                new_title = appointment.service.title
            else:
                new_title = appointment.service.title

            updated += 1
            if dry_run:
                continue
            appointment.title = new_title
            appointment.save(update_fields=["title"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. updated={updated}, dry_run={dry_run}"
            )
        )
