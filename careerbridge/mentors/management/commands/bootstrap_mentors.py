from django.core.management.base import BaseCommand
from datetime import time

from mentors.models import (
    MentorProfile,
    MentorService,
    MentorAvailability,
)

DEFAULT_PRICE = 49


class Command(BaseCommand):
    help = "Bootstrap approved mentors: profile, default service, availability rules (idempotent)"

    def handle(self, *args, **options):
        mentors = MentorProfile.objects.filter(status="approved")

        self.stdout.write(
            self.style.NOTICE(f"🔧 Bootstrapping {mentors.count()} approved mentors")
        )

        for mentor in mentors:
            self.bootstrap_profile(mentor)
            self.bootstrap_service(mentor)
            self.bootstrap_availability(mentor)

        self.stdout.write(self.style.SUCCESS("✅ Mentor bootstrap completed"))

    # =========================================================
    # Profile
    # =========================================================
    def bootstrap_profile(self, mentor):
        updated_fields = []

        if not mentor.headline:
            mentor.headline = self.generate_headline(mentor)
            updated_fields.append("headline")

        if mentor.starting_price == 0:
            mentor.starting_price = DEFAULT_PRICE
            updated_fields.append("starting_price")

        if updated_fields:
            mentor.save(update_fields=updated_fields)
            self.stdout.write(
                f"✔ Profile updated for mentor {mentor.id}: {', '.join(updated_fields)}"
            )

    def generate_headline(self, mentor):
        if mentor.years_of_experience and mentor.industry:
            return f"{mentor.years_of_experience}+ years in {mentor.industry}"
        return "Career Mentor | Resume Review & Mock Interview"

    # =========================================================
    # Service
    # =========================================================
    def bootstrap_service(self, mentor):
        # 已有 active service 就不再创建（幂等）
        if MentorService.objects.filter(mentor=mentor, is_active=True).exists():
            return

        MentorService.objects.create(
            mentor=mentor,
            service_type="resume_review",
            title="Resume Review",
            description="One-on-one resume review with actionable feedback.",
            pricing_model="hourly",
            price_per_hour=mentor.starting_price or DEFAULT_PRICE,
            duration_minutes=60,
            is_active=True,
        )

        self.stdout.write(f"✔ Default service created for mentor {mentor.id}")

    # =========================================================
    # Availability (rule-based, not datetime slots)
    # =========================================================
    def bootstrap_availability(self, mentor):
        created = 0

        # Monday–Friday, 18:00–21:00
        for day in range(0, 5):
            start = time(18, 0)
            end = time(21, 0)

            exists = MentorAvailability.objects.filter(
                mentor=mentor,
                day_of_week=day,
                start_time=start,
            ).exists()

            if not exists:
                MentorAvailability.objects.create(
                    mentor=mentor,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    is_active=True,
                )
                created += 1

        if created:
            self.stdout.write(
                f"✔ {created} availability rules created for mentor {mentor.id}"
            )
