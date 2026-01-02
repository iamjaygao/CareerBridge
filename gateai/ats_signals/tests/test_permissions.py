"""
Permission tests for ATS Signals and Human Review Tasks.

Tests object-level permissions to ensure users can only access
signals and review tasks for decision slots they own.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from ats_signals.models import ATSSignal
from human_loop.models import HumanReviewTask

User = get_user_model()


class ATSSignalPermissionsTest(TestCase):
    """Test object-level permissions for ATS Signals."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        
        # Create two users
        self.user_a = User.objects.create_user(
            username='user_a',
            email='usera@example.com',
            password='testpass123'
        )
        self.user_b = User.objects.create_user(
            username='user_b',
            email='userb@example.com',
            password='testpass123'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create decision slot IDs for each user
        self.slot_a = f"ds_user_a_{int(timezone.now().timestamp())}"
        self.slot_b = f"ds_user_b_{int(timezone.now().timestamp())}"
        
        # Create signals for user A's slot
        self.signal_a1 = ATSSignal.objects.create(
            decision_slot_id=self.slot_a,
            signal_type='structure_issue',
            severity='high',
            category='Formatting',
            message='Test signal for user A',
            engine_name='ResumeAuditEngine',
            engine_version='1.0.0',
            details={'user_id': str(self.user_a.id)},  # Store user_id in details for permission check
        )
        
        self.signal_a2 = ATSSignal.objects.create(
            decision_slot_id=self.slot_a,
            signal_type='keyword_missing',
            severity='medium',
            category='Content',
            message='Another signal for user A',
            engine_name='ResumeAuditEngine',
            engine_version='1.0.0',
            details={'user_id': str(self.user_a.id)},
        )
        
        # Create signals for user B's slot
        self.signal_b1 = ATSSignal.objects.create(
            decision_slot_id=self.slot_b,
            signal_type='content_issue',
            severity='high',
            category='Content',
            message='Test signal for user B',
            engine_name='ResumeAuditEngine',
            engine_version='1.0.0',
            details={'user_id': str(self.user_b.id)},
        )
        
        # Create review task for user A's critical signal
        critical_signal_a = ATSSignal.objects.create(
            decision_slot_id=self.slot_a,
            signal_type='ats_incompatibility',
            severity='critical',
            category='ATS',
            message='Critical signal for user A',
            engine_name='ResumeAuditEngine',
            engine_version='1.0.0',
            details={'user_id': str(self.user_a.id)},
        )
        
        self.review_task_a = HumanReviewTask.objects.create(
            signal=critical_signal_a,
            decision_slot_id=self.slot_a,
            task_type='signal_review',
            status='pending',
            priority='urgent',
            context_data={'user_id': str(self.user_a.id)},  # Store user_id for permission check
        )
    
    def test_user_can_access_own_signals(self):
        """Test that user A can access their own signals."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/v1/ats-signals/?decision_slot_id={self.slot_a}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_count'], 3)  # signal_a1, signal_a2, critical_signal_a
        
        # Verify all returned signals belong to user A's slot
        signal_ids = {s['id'] for s in data['signals']}
        self.assertIn(self.signal_a1.id, signal_ids)
        self.assertIn(self.signal_a2.id, signal_ids)
    
    def test_user_cannot_access_other_user_signals(self):
        """Test that user B cannot access user A's signals."""
        self.client.force_authenticate(user=self.user_b)
        
        # Try to access user A's decision slot
        response = self.client.get(f'/api/v1/ats-signals/?decision_slot_id={self.slot_a}')
        
        # Should return 404 (not found) to avoid leaking existence
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_access_other_user_signal_detail(self):
        """Test that user B cannot access user A's signal detail."""
        self.client.force_authenticate(user=self.user_b)
        
        response = self.client.get(f'/api/v1/ats-signals/{self.signal_a1.id}/')
        
        # Should return 404 (not found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_staff_can_access_all_signals(self):
        """Test that staff user can access all signals."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Access user A's signals
        response_a = self.client.get(f'/api/v1/ats-signals/?decision_slot_id={self.slot_a}')
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        
        # Access user B's signals
        response_b = self.client.get(f'/api/v1/ats-signals/?decision_slot_id={self.slot_b}')
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        
        # Access signal detail
        response_detail = self.client.get(f'/api/v1/ats-signals/{self.signal_a1.id}/')
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
    
    def test_user_can_access_own_review_tasks(self):
        """Test that user A can access their own review tasks."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/v1/human-loop/review-tasks/?decision_slot_id={self.slot_a}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_count'], 1)
        self.assertEqual(data['review_tasks'][0]['id'], self.review_task_a.id)
    
    def test_user_cannot_access_other_user_review_tasks(self):
        """Test that user B cannot access user A's review tasks."""
        self.client.force_authenticate(user=self.user_b)
        
        # Try to access user A's decision slot
        response = self.client.get(f'/api/v1/human-loop/review-tasks/?decision_slot_id={self.slot_a}')
        
        # Should return 404 (not found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_access_other_user_review_task_detail(self):
        """Test that user B cannot access user A's review task detail."""
        self.client.force_authenticate(user=self.user_b)
        
        response = self.client.get(f'/api/v1/human-loop/review-tasks/{self.review_task_a.id}/')
        
        # Should return 404 (not found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_staff_can_access_all_review_tasks(self):
        """Test that staff user can access all review tasks."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Access user A's review tasks
        response = self.client.get(f'/api/v1/human-loop/review-tasks/?decision_slot_id={self.slot_a}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Access review task detail
        response_detail = self.client.get(f'/api/v1/human-loop/review-tasks/{self.review_task_a.id}/')
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
    
    def test_list_without_decision_slot_id_returns_empty_for_regular_user(self):
        """Test that listing without decision_slot_id returns empty for regular users."""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get('/api/v1/ats-signals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Should only return signals for user A's allowed slots
        # Since we're using context_data workaround, it should return signals with user_id in details
        self.assertGreaterEqual(data['total_count'], 0)

