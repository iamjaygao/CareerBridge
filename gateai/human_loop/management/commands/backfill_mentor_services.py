from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from human_loop.models import MentorProfile, MentorService


HERO_TYPE = "mentoring_session"
FOLLOWUP_TYPE = "follow_up"

DEFAULT_PRICE = Decimal("100.00")


class Command(BaseCommand):
    help = "Backfill mentor services to ensure each mentor has a hero service and a follow-up service."

    def handle(self, *args, **options):
        mentors = MentorProfile.objects.all()
        self.stdout.write(f"Found {mentors.count()} mentors")

        for mentor in mentors:
            with transaction.atomic():
                self._backfill_for_mentor(mentor)

        self.stdout.write(self.style.SUCCESS("✅ Mentor services backfill completed"))

    def _backfill_for_mentor(self, mentor: MentorProfile):
        services = mentor.services.all()
        existing_types = set(
            services.values_list("service_type", flat=True)
        )

        hero_service = None

        # -----------------------------
        # 1. HERO SERVICE
        # -----------------------------
        if HERO_TYPE in existing_types:
            hero_service = services.filter(service_type=HERO_TYPE).first()
        else:
            hero_price = mentor.starting_price or DEFAULT_PRICE

            hero_service = MentorService.objects.create(
                mentor=mentor,
                service_type=HERO_TYPE,
                title=(
                    mentor.primary_focus
                    or mentor.headline
                    or "1-on-1 Mentorship Session"
                ),
                description=(
                    mentor.session_focus
                    or "One-on-one mentoring session with actionable feedback."
                ),
                pricing_model="hourly",
                price_per_hour=hero_price,
                duration_minutes=60,
                is_active=True,
            )

            self.stdout.write(
                f"➕ Created HERO service for mentor {mentor.id}"
            )

        # Ensure primary_service_id is set correctly
        if mentor.primary_service_id != hero_service.id:
            mentor.primary_service_id = hero_service.id
            mentor.save(update_fields=["primary_service_id"])

        # -----------------------------
        # 2. FOLLOW-UP SERVICE
        # -----------------------------
        if FOLLOWUP_TYPE not in existing_types:
            followup_price = (
                hero_service.price_per_hour or DEFAULT_PRICE
            ) * Decimal("0.8")

            MentorService.objects.create(
                mentor=mentor,
                service_type=FOLLOWUP_TYPE,
                title="Follow-up Session",
                description="Short follow-up session to continue progress.",
                pricing_model="hourly",
                price_per_hour=followup_price,
                duration_minutes=30,
                is_active=True,
            )

            self.stdout.write(
                f"➕ Created FOLLOW-UP service for mentor {mentor.id}"
            )

        # -----------------------------
        # 3. Safety check
        # -----------------------------
        final_count = mentor.services.filter(is_active=True).count()
        if final_count < 2:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Mentor {mentor.id} has only {final_count} active services"
                )
            )
