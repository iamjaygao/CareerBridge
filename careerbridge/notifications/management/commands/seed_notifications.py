"""
Management command to seed test notifications for all roles
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from users.models import User


class Command(BaseCommand):
    help = 'Seed test notifications for all roles'

    def handle(self, *args, **options):
        self.stdout.write('Creating seed notifications...')

        # Get or create a super admin user for user-specific notifications
        superadmin_user = User.objects.filter(role='superadmin').first()
        admin_user = User.objects.filter(role='admin').first()
        staff_user = User.objects.filter(role='staff').first()
        mentor_user = User.objects.filter(role='mentor').first()
        student_user = User.objects.filter(role='student').first()

        notifications_created = 0

        # 1. Super Admin Notifications
        Notification.objects.get_or_create(
            title='System Initialized',
            defaults={
                'target_role': 'superadmin',
                'notification_type': 'system_announcement',
                'message': 'CareerBridge system has been successfully initialized. All core services are operational.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=2),
            }
        )
        notifications_created += 1

        Notification.objects.get_or_create(
            title='New Mentor Applications Rising Rapidly',
            defaults={
                'target_role': 'superadmin',
                'notification_type': 'system_announcement',
                'message': 'Mentor applications have increased by 45% in the last 24 hours. Consider reviewing the approval queue.',
                'priority': 'high',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=1),
            }
        )
        notifications_created += 1

        Notification.objects.get_or_create(
            title='AI Engine Latency Above Threshold',
            defaults={
                'target_role': 'superadmin',
                'notification_type': 'system_announcement',
                'message': 'AI engine response time is currently 2.3s (threshold: 2.0s). Consider scaling resources.',
                'priority': 'critical',
                'is_read': False,
                'created_at': timezone.now() - timedelta(minutes=30),
            }
        )
        notifications_created += 1

        # 2. Admin Notifications
        Notification.objects.get_or_create(
            title='New Mentor Verification Requested',
            defaults={
                'target_role': 'admin',
                'notification_type': 'mentor_response',
                'message': 'A new mentor has submitted their verification documents. Please review and approve.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=3),
            }
        )
        notifications_created += 1

        Notification.objects.get_or_create(
            title='New Appointment Created',
            defaults={
                'target_role': 'admin',
                'notification_type': 'appointment_confirmed',
                'message': 'A new appointment has been scheduled between a student and mentor.',
                'priority': 'low',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=1),
            }
        )
        notifications_created += 1

        # 3. Staff Notifications
        Notification.objects.get_or_create(
            title='New Resume Review Assigned',
            defaults={
                'target_role': 'staff',
                'notification_type': 'resume_analysis_complete',
                'message': 'A new resume has been submitted and requires your review. Please check the review queue.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=2),
            }
        )
        notifications_created += 1

        # 4. Mentor Notifications
        Notification.objects.get_or_create(
            title='Student Booked Appointment',
            defaults={
                'target_role': 'mentor',
                'notification_type': 'appointment_confirmed',
                'message': 'A student has booked an appointment with you. Check your calendar for details.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=4),
            }
        )
        notifications_created += 1

        if mentor_user:
            Notification.objects.get_or_create(
                title='Appointment Reminder',
                defaults={
                    'user': mentor_user,
                    'target_role': None,
                    'notification_type': 'appointment_reminder',
                    'message': 'You have an appointment scheduled in 2 hours. Please prepare accordingly.',
                    'priority': 'high',
                    'is_read': False,
                    'created_at': timezone.now() - timedelta(minutes=15),
                }
            )
            notifications_created += 1

        # 5. Student Notifications
        Notification.objects.get_or_create(
            title='Appointment Accepted',
            defaults={
                'target_role': 'student',
                'notification_type': 'appointment_confirmed',
                'message': 'Your appointment request has been accepted by your mentor. See details in your appointments.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=5),
            }
        )
        notifications_created += 1

        Notification.objects.get_or_create(
            title='Resume Reviewed',
            defaults={
                'target_role': 'student',
                'notification_type': 'resume_analysis_complete',
                'message': 'Your resume has been reviewed and analyzed. Check your resume dashboard for feedback.',
                'priority': 'normal',
                'is_read': False,
                'created_at': timezone.now() - timedelta(hours=6),
            }
        )
        notifications_created += 1

        if student_user:
            Notification.objects.get_or_create(
                title='Welcome to CareerBridge!',
                defaults={
                    'user': student_user,
                    'target_role': None,
                    'notification_type': 'welcome',
                    'message': 'Welcome to CareerBridge! Start by exploring mentors, uploading your resume, or booking your first appointment.',
                    'priority': 'normal',
                    'is_read': False,
                    'created_at': timezone.now() - timedelta(days=1),
                }
            )
            notifications_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {notifications_created} seed notifications'
            )
        )

