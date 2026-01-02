from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from signal_delivery.models import Notification
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import (
    NotificationType,
    Role,
    get_db_type,
    get_notification_rule,
    is_system_event,
)


class Command(BaseCommand):
    help = "Seed notifications for all configured notification rules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-type",
            type=int,
            default=1,
            help="How many notifications to create per type/recipient.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned changes without writing to the database.",
        )

    def _get_or_create_user(self, role: Role):
        User = get_user_model()
        user = User.objects.filter(role=role.value).order_by("id").first()
        if user:
            return user
        username = f"seed_{role.value}"
        user = User(
            username=username,
            email=f"{username}@example.com",
            role=role.value,
            is_staff=role in {Role.ADMIN, Role.STAFF, Role.SUPERADMIN},
            is_superuser=role == Role.SUPERADMIN,
        )
        user.set_password("123456789")
        user.save()
        return user

    def handle(self, *args, **options):
        per_type = max(1, options["per_type"])
        dry_run = options["dry_run"]

        created = 0
        created_by_role = {role.value: 0 for role in Role}
        users = {role: self._get_or_create_user(role) for role in Role}

        for event in NotificationType:
            rule = get_notification_rule(event)
            if dry_run:
                created += per_type * len(rule.recipients)
                for role in rule.recipients:
                    created_by_role[role.value] += per_type
                continue

            context = {
                "appointment_id": 1,
                "mentor_application_id": 1,
                "resume_id": 1,
                "payment_id": 1,
                "support_ticket_id": 1,
                "feedback_id": 1,
                "report_id": 1,
                "conversation_id": 1,
                "metric_key": "seed_metric",
                "incident_id": "seed_incident",
                "change_id": "seed_change",
                "user_id": users[Role.STUDENT].id,
                "mentor_id": 1,
            }
            for role in Role:
                context[role.value] = users[role]

            for _ in range(per_type):
                notify(
                    event,
                    context=context if not is_system_event(event) else {},
                    title=f"[Seed] {event.value}",
                    message=f"[Seed] {event.value}",
                    priority="normal",
                    payload={"seed": True, "event": event.value},
                )
                created += 1
                for role in rule.recipients:
                    created_by_role[role.value] += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. "
                f"created={created}, per_role={created_by_role}, dry_run={dry_run}"
            )
        )
