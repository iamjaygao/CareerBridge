"""
Management command to seed system notifications only.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from signal_delivery.models import Notification

class Command(BaseCommand):
    help = 'Seed test notifications for all roles and flows'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Creating seed notifications...')

        notifications_created = 0

        # ------------------------------------------------------------------
        # SYSTEM-ONLY SEED NOTIFICATIONS
        # ------------------------------------------------------------------
        Notification.objects.get_or_create(
            title='System Initialized',
            defaults={
                'target_role': 'superadmin',
                'notification_type': 'system_announcement',
                'message': 'CareerBridge system has been successfully initialized.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=2),
            }
        ); notifications_created += 1

        Notification.objects.get_or_create(
            title='AI Engine Latency Alert',
            defaults={
                'target_role': 'superadmin',
                'notification_type': 'system_announcement',
                'message': 'AI engine latency exceeded threshold (2.3s).',
                'priority': 'critical',
                'created_at': timezone.now() - timedelta(minutes=30),
            }
        ); notifications_created += 1

        Notification.objects.get_or_create(
            title='Scheduled Maintenance Notice',
            defaults={
                'target_role': 'admin',
                'notification_type': 'system_announcement',
                'message': 'Maintenance is scheduled for tonight at 02:00 UTC.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=1),
            }
        ); notifications_created += 1

        Notification.objects.get_or_create(
            title='Compliance Reminder',
            defaults={
                'target_role': 'staff',
                'notification_type': 'system_announcement',
                'message': 'Reminder: monthly compliance audit is due this week.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=4),
            }
        ); notifications_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully created {notifications_created} seed notifications'
            )
        )
