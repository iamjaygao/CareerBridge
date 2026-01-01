from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from .models import TimeSlot, Appointment, AppointmentRequest
from mentors.models import MentorProfile, MentorService

User = get_user_model()

class AppointmentModelTest(TestCase):
    """Appointment model test"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.mentor = MentorProfile.objects.create(
            user=self.user,
            bio='Test mentor',
            years_of_experience=5,
            current_position='Senior Developer',
            industry='Technology'
        )
        
        self.time_slot = TimeSlot.objects.create(
            mentor=self.mentor,
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            price=50.00,
            currency='USD'
        )
    
    def test_time_slot_creation(self):
        """Test time slot creation"""
        self.assertEqual(self.time_slot.mentor, self.mentor)
        self.assertEqual(self.time_slot.price, 50.00)
        self.assertTrue(self.time_slot.is_bookable)
        self.assertEqual(self.time_slot.duration_minutes, 60)
    
    def test_appointment_creation(self):
        """Test appointment creation"""
        appointment = Appointment.objects.create(
            user=self.user,
            mentor=self.mentor,
            time_slot=self.time_slot,
            title='Test Appointment',
            description='Test description',
            scheduled_start=self.time_slot.start_time,
            scheduled_end=self.time_slot.end_time,
            price=self.time_slot.price,
            currency=self.time_slot.currency
        )
        
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.mentor, self.mentor)
        self.assertEqual(appointment.status, 'pending')
        self.assertTrue(appointment.is_upcoming)
        # Fix: appointment time too close, cannot cancel (requires 24 hours notice)
        self.assertFalse(appointment.can_cancel)
    
    def test_appointment_request_creation(self):
        """Test appointment request creation"""
        request = AppointmentRequest.objects.create(
            user=self.user,
            mentor=self.mentor,
            preferred_date=timezone.now().date() + timedelta(days=1),
            preferred_time_start=datetime.strptime('10:00', '%H:%M').time(),
            preferred_time_end=datetime.strptime('11:00', '%H:%M').time(),
            title='Test Request',
            description='Test request description',
            topics=['Career Advice', 'Interview Preparation'],
            expires_at=timezone.now() + timedelta(days=7)  # Add expiration time
        )
        
        self.assertEqual(request.user, self.user)
        self.assertEqual(request.mentor, self.mentor)
        self.assertEqual(request.status, 'pending')
        self.assertFalse(request.is_expired)


class AppointmentLockReleaseTest(TestCase):
    """Appointment lock release flow test"""

    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user(
            username='studentuser',
            email='student@example.com',
            password='testpass123'
        )
        self.mentor_user = User.objects.create_user(
            username='mentoruser',
            email='mentor@example.com',
            password='testpass123'
        )
        self.mentor = MentorProfile.objects.create(
            user=self.mentor_user,
            bio='Mentor bio',
            years_of_experience=5,
            current_position='Senior Developer',
            industry='Technology'
        )
        self.service = MentorService.objects.create(
            mentor=self.mentor,
            service_type='career_consultation',
            title='Career Consultation',
            description='Test service',
            pricing_model='hourly',
            price_per_hour=50.00,
            duration_minutes=60,
            is_active=True,
        )
        self.time_slot = TimeSlot.objects.create(
            mentor=self.mentor,
            start_time=timezone.now() + timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=3),
            price=50.00,
            currency='USD'
        )
        self.client.force_authenticate(user=self.student)

    def test_release_lock_after_payment_failure(self):
        lock_response = self.client.post(
            '/api/v1/appointments/lock-slot/',
            {
                'time_slot_id': self.time_slot.id,
                'service_id': self.service.id,
                'title': 'Test Session',
                'description': '',
            },
            format='json'
        )
        self.assertEqual(lock_response.status_code, 201)
        appointment_id = lock_response.data['appointment']['id']

        release_response = self.client.post(
            '/api/v1/appointments/lock-slot/',
            {
                'appointment_id': appointment_id,
                'action': 'release',
            },
            format='json'
        )
        self.assertEqual(release_response.status_code, 200)
        self.time_slot.refresh_from_db()
        appointment = Appointment.objects.get(id=appointment_id)
        self.assertEqual(appointment.status, 'expired')
        self.assertTrue(self.time_slot.is_available)

        release_again = self.client.post(
            '/api/v1/appointments/lock-slot/',
            {
                'appointment_id': appointment_id,
                'action': 'release',
            },
            format='json'
        )
        self.assertEqual(release_again.status_code, 200)
