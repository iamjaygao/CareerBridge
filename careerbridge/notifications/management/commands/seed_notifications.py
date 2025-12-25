"""
Management command to seed test notifications for all roles
Covers:
- role-based notifications
- user-specific notifications
- business-triggered notifications
- payload-based action notifications
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification
from users.models import User
from appointments.models import Appointment


class Command(BaseCommand):
    help = 'Seed test notifications for all roles and flows'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Creating seed notifications...')

        # Fetch users by role
        superadmin_user = User.objects.filter(role='superadmin').first()
        admin_user = User.objects.filter(role='admin').first()
        staff_user = User.objects.filter(role='staff').first()
        mentor_user = User.objects.filter(role='mentor').first()
        student_user = User.objects.filter(role='student').first()

        appointment = Appointment.objects.first()

        notifications_created = 0

        # ------------------------------------------------------------------
        # 1. SUPER ADMIN – system level
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

        # ------------------------------------------------------------------
        # 2. ADMIN – platform operations
        # ------------------------------------------------------------------
        Notification.objects.get_or_create(
            title='New Mentor Verification Requested',
            defaults={
                'target_role': 'admin',
                'notification_type': 'mentor_response',
                'message': 'A mentor submitted verification documents.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=3),
            }
        ); notifications_created += 1

        # ------------------------------------------------------------------
        # 3. STAFF – task oriented
        # ------------------------------------------------------------------
        Notification.objects.get_or_create(
            title='Resume Review Assigned',
            defaults={
                'target_role': 'staff',
                'notification_type': 'resume_analysis_complete',
                'message': 'A resume requires your review.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=2),
            }
        ); notifications_created += 1

        # ------------------------------------------------------------------
        # 4. MENTOR – business notifications
        # ------------------------------------------------------------------
        if mentor_user and student_user:
            Notification.objects.get_or_create(
                title='New Appointment Request',
                defaults={
                    'user': mentor_user,
                    'notification_type': 'mentor_response',
                    'message': f'{student_user.first_name} sent you an appointment request.',
                    'priority': 'normal',
                    'created_at': timezone.now() - timedelta(minutes=20),
                }
            ); notifications_created += 1

        Notification.objects.get_or_create(
            title='Appointment Booked',
            defaults={
                'target_role': 'mentor',
                'notification_type': 'appointment_confirmed',
                'message': 'A student booked an appointment with you.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=4),
            }
        ); notifications_created += 1

        # ------------------------------------------------------------------
        # 5. STUDENT – core UX notifications
        # ------------------------------------------------------------------
        Notification.objects.get_or_create(
            title='Appointment Accepted',
            defaults={
                'target_role': 'student',
                'notification_type': 'appointment_confirmed',
                'message': 'Your appointment request was accepted.',
                'priority': 'normal',
                'created_at': timezone.now() - timedelta(hours=5),
            }
        ); notifications_created += 1

        if student_user:
            Notification.objects.get_or_create(
                title='Welcome to CareerBridge!',
                defaults={
                    'user': student_user,
                    'notification_type': 'welcome',
                    'message': 'Explore mentors, upload your resume, or book your first session.',
                    'priority': 'normal',
                    'created_at': timezone.now() - timedelta(days=1),
                }
            ); notifications_created += 1

        # ------------------------------------------------------------------
        # 6. ⭐ PAYLOAD / ACTION NOTIFICATION (MOST IMPORTANT)
        # ------------------------------------------------------------------
        if student_user and appointment:
            Notification.objects.get_or_create(
                title='Please review your session',
                defaults={
                    'user': student_user,
                    'notification_type': 'system_announcement',
                    'message': 'Please leave a review for your completed session.',
                    'priority': 'normal',
                    'related_appointment': appointment,
                    'payload': {
                        'action': 'review_appointment',
                        'appointment_id': appointment.id,
                    },
                    'created_at': timezone.now() - timedelta(minutes=10),
                }
            ); notifications_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully created {notifications_created} seed notifications'
            )
        )
