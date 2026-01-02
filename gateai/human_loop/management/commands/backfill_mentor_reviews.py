from django.core.management.base import BaseCommand
from django.db.models import Avg, Count

from decision_slots.models import Appointment
from human_loop.models import MentorReview, MentorProfile


class Command(BaseCommand):
    help = "Backfill MentorReview records from appointment ratings/feedback."

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
            help="Only backfill reviews for a specific mentor ID.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        mentor_id = options["mentor_id"]

        appointments = Appointment.objects.filter(
            user_rating__isnull=False
        ).select_related("mentor", "user")
        if mentor_id:
            appointments = appointments.filter(mentor_id=mentor_id)

        created = 0
        updated = 0

        for appointment in appointments:
            defaults = {
                "rating": appointment.user_rating,
                "comment": appointment.user_feedback or "",
            }
            if dry_run:
                if MentorReview.objects.filter(
                    mentor=appointment.mentor,
                    user=appointment.user,
                ).exists():
                    updated += 1
                else:
                    created += 1
                continue

            review, was_created = MentorReview.objects.update_or_create(
                mentor=appointment.mentor,
                user=appointment.user,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        if not dry_run:
            mentors = MentorProfile.objects.all()
            if mentor_id:
                mentors = mentors.filter(id=mentor_id)
            for mentor in mentors:
                summary = MentorReview.objects.filter(mentor=mentor).aggregate(
                    average=Avg("rating"),
                    total=Count("id"),
                )
                mentor.average_rating = summary["average"] or 0
                mentor.total_reviews = summary["total"] or 0
                mentor.save(update_fields=["average_rating", "total_reviews"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. created={created}, updated={updated}, dry_run={dry_run}"
            )
        )
