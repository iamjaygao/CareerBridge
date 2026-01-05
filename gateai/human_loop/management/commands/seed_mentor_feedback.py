import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from django.utils import timezone

from appointments.models import Appointment, TimeSlot
from human_loop.models import MentorProfile, MentorReview, MentorService


class Command(BaseCommand):
    help = "Seed mentor reviews and optional appointment feedback data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-mentor",
            type=int,
            default=5,
            help="Target number of reviews per mentor.",
        )
        parser.add_argument(
            "--mentor-id",
            type=int,
            default=None,
            help="Only seed for a specific mentor ID.",
        )
        parser.add_argument(
            "--no-appointments",
            action="store_true",
            help="Do not create appointment records.",
        )

    def handle(self, *args, **options):
        per_mentor = max(1, options["per_mentor"])
        mentor_id = options["mentor_id"]
        create_appointments = not options["no_appointments"]

        User = get_user_model()
        students = list(User.objects.filter(role="student").order_by("id"))

        mentors = MentorProfile.objects.all()
        if mentor_id:
            mentors = mentors.filter(id=mentor_id)

        created_reviews = 0
        created_appointments = 0

        for mentor in mentors:
            service = mentor.services.filter(is_active=True).first()
            if not service:
                service = MentorService.objects.create(
                    mentor=mentor,
                    service_type="career_consultation",
                    title="Career Consultation",
                    description="One-on-one career consultation session.",
                    pricing_model="fixed",
                    fixed_price=Decimal("79.00"),
                    duration_minutes=60,
                )

            existing_reviews = MentorReview.objects.filter(mentor=mentor).count()
            needed = max(0, per_mentor - existing_reviews)
            if needed == 0:
                continue

            used_user_ids = set(
                MentorReview.objects.filter(mentor=mentor).values_list("user_id", flat=True)
            )

            for index in range(needed):
                if students and len(used_user_ids) < len(students):
                    student = next(user for user in students if user.id not in used_user_ids)
                else:
                    student = User.objects.create(
                        username=f"seed_student_{mentor.id}_{index}",
                        email=f"seed_student_{mentor.id}_{index}@example.com",
                        role="student",
                        first_name="Seed",
                        last_name="Student",
                    )
                    students.append(student)

                used_user_ids.add(student.id)

                rating = random.choice([3, 4, 4, 5, 5])
                comment = random.choice(
                    [
                        "Helpful session with actionable feedback.",
                        "Great insights and clear next steps.",
                        "Very practical advice and guidance.",
                        "Strong mentor with detailed feedback.",
                        "Would book again for follow-up.",
                    ]
                )

                MentorReview.objects.create(
                    mentor=mentor,
                    user=student,
                    rating=rating,
                    comment=comment,
                )
                created_reviews += 1

                if create_appointments:
                    start_time = timezone.now() - timezone.timedelta(days=random.randint(1, 60))
                    end_time = start_time + timezone.timedelta(minutes=service.duration_minutes)
                    price = (
                        service.fixed_price
                        if service.pricing_model == "fixed" and service.fixed_price
                        else Decimal("79.00")
                    )

                    slot = TimeSlot.objects.create(
                        mentor=mentor,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=False,
                        max_bookings=1,
                        current_bookings=1,
                        price=price,
                        currency="USD",
                    )

                    Appointment.objects.create(
                        user=student,
                        mentor=mentor,
                        time_slot=slot,
                        service=service,
                        title=service.title,
                        description="Seeded appointment",
                        status="completed",
                        scheduled_start=start_time,
                        scheduled_end=end_time,
                        price=price,
                        currency="USD",
                        is_paid=True,
                        user_rating=rating,
                        user_feedback=comment,
                    )
                    created_appointments += 1

            summary = MentorReview.objects.filter(mentor=mentor).aggregate(
                average=Avg("rating"),
                total=Count("id"),
            )
            mentor.average_rating = summary["average"] or 0
            mentor.total_reviews = summary["total"] or 0
            mentor.save(update_fields=["average_rating", "total_reviews"])

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. reviews_created="
                f"{created_reviews}, appointments_created={created_appointments}"
            )
        )
