import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from adminpanel.models import ContentItem, SupportTicket


class Command(BaseCommand):
    help = "Seed staff-facing content items and support tickets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--content-count",
            type=int,
            default=5,
            help="Number of content items to create.",
        )
        parser.add_argument(
            "--ticket-count",
            type=int,
            default=6,
            help="Number of support tickets to create.",
        )
        parser.add_argument(
            "--staff-username",
            type=str,
            default="seed_staff",
            help="Username to use/create for staff ownership.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned changes without writing to the database.",
        )

    def handle(self, *args, **options):
        content_count = max(0, options["content_count"])
        ticket_count = max(0, options["ticket_count"])
        staff_username = options["staff_username"]
        dry_run = options["dry_run"]

        User = get_user_model()

        staff_user = (
            User.objects.filter(role="staff").order_by("id").first()
            or User.objects.filter(is_staff=True).order_by("id").first()
        )

        if not staff_user:
            staff_user = User(
                username=staff_username,
                email=f"{staff_username}@example.com",
                role="staff",
                is_staff=True,
            )
            staff_user.set_password("123456789")
            if not dry_run:
                staff_user.save()
            self.stdout.write(self.style.WARNING(f"Created staff user: {staff_user.username}"))

        student_users = list(User.objects.filter(role="student").order_by("id")[:max(1, ticket_count)])
        if len(student_users) < ticket_count:
            for index in range(ticket_count - len(student_users)):
                username = f"seed_support_student_{index + 1}"
                student = User(
                    username=username,
                    email=f"{username}@example.com",
                    role="student",
                )
                student.set_password("123456789")
                if not dry_run:
                    student.save()
                student_users.append(student)

        content_templates = [
            ("Top Interview Prep Checklist", "guide"),
            ("Resume Optimization Tips", "blog"),
            ("Career Roadmap for Engineers", "resource"),
            ("Behavioral Interview Guide", "guide"),
            ("System Design Study Plan", "blog"),
        ]

        ticket_templates = [
            ("Unable to book session", "User reports booking fails with a 500 error."),
            ("Payment failed", "Card payment keeps failing for valid cards."),
            ("Profile update error", "User cannot save profile changes."),
            ("Mentor availability mismatch", "Calendar times do not match booking slots."),
            ("Email verification issue", "Verification email not delivered."),
            ("Refund request", "User asks about refund for cancelled session."),
        ]

        created_content = 0
        created_tickets = 0

        for index in range(content_count):
            title, content_type = content_templates[index % len(content_templates)]
            status = random.choice(["draft", "published"])
            summary = "Staff-seeded content summary for quick review."
            body = "Staff-seeded content body. Replace with real copy as needed."

            if not dry_run:
                ContentItem.objects.create(
                    title=f"{title} #{index + 1}",
                    summary=summary,
                    body=body,
                    content_type=content_type,
                    status=status,
                    author=staff_user,
                )
            created_content += 1

        priorities = ["low", "medium", "high", "urgent"]
        statuses = ["open", "in_progress", "resolved"]

        for index in range(ticket_count):
            issue, description = ticket_templates[index % len(ticket_templates)]
            user = student_users[index % len(student_users)]
            priority = random.choice(priorities)
            status = random.choice(statuses)

            if not dry_run:
                SupportTicket.objects.create(
                    user=user,
                    issue=issue,
                    description=description,
                    priority=priority,
                    status=status,
                    assigned_staff=staff_user if status != "open" else None,
                    staff_notes="Seeded ticket for staff workflow testing.",
                )
            created_tickets += 1

        mode = "dry_run=True" if dry_run else "dry_run=False"
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. content_created={created_content}, tickets_created={created_tickets}, {mode}"
            )
        )
