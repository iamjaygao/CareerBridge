from django.core.management.base import BaseCommand
from django.db import transaction

from appointments.models import Appointment
from mentors.models import MentorService


class Command(BaseCommand):
    help = "Backfill Appointment.service for existing records"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of appointments processed')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        qs = Appointment.objects.filter(service__isnull=True).select_related('mentor')
        if limit:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No appointments to backfill.'))
            return

        updated = 0
        for appt in qs:
            mentor = appt.mentor
            service = None

            if mentor:
                # Prefer exact title match among active services
                if appt.title:
                    service = MentorService.objects.filter(
                        mentor=mentor,
                        is_active=True,
                        title=appt.title
                    ).first()

                # Fallback to mentor primary service
                if not service and mentor.primary_service_id:
                    service = MentorService.objects.filter(
                        id=mentor.primary_service_id,
                        mentor=mentor,
                        is_active=True
                    ).first()

            if service:
                updated += 1
                if not dry_run:
                    with transaction.atomic():
                        Appointment.objects.filter(id=appt.id, service__isnull=True).update(service=service)

        if dry_run:
            self.stdout.write(self.style.WARNING(f'Dry run: would update {updated} of {total} appointments.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated} of {total} appointments.'))
