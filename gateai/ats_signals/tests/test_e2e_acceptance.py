"""
End-to-End Acceptance Test for ATS Signals + Human Loop.

Tests the complete OS flow:
1. User creation
2. DecisionSlot creation (TODO: DecisionSlot model doesn't exist - using string ID)
3. Engine HTTP endpoint call
4. Signal persistence
5. Human loop activation (if critical signals)

This is a deterministic, local E2E test with no external services.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from ats_signals.models import ATSSignal
from human_loop.models import HumanReviewTask

User = get_user_model()


class E2EAcceptanceTest(TestCase):
    """
    End-to-end acceptance test for the complete ATS Signals + Human Loop flow.
    
    Exercises the full OS path from HTTP engine endpoint -> persistence -> human loop.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='test_student',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # TODO: DecisionSlot model doesn't exist in decision_slots app.
        # Currently, decision_slot_id is just a string identifier.
        # When DecisionSlot model is created, update this test to:
        # 1. Create a real DecisionSlot instance with user=self.user
        # 2. Use decision_slot.id instead of string ID
        # 3. Verify ownership through DecisionSlot.user field
        self.decision_slot_id = f"ds_e2e_test_{int(timezone.now().timestamp())}"
    
    def test_full_e2e_flow_with_critical_signal(self):
        """
        Test complete E2E flow including critical signal -> human loop activation.
        
        Scenario:
        1. Call engine endpoint with resume text that produces critical signals
        2. Verify signals are persisted
        3. Verify human review task is created for critical signals
        """
        # Step 1: Call engine HTTP endpoint
        engine_url = '/api/engines/signal-core/resume-audit/'
        
        # Resume text designed to produce critical signals (missing contact info, no keywords, etc.)
        resume_text = """
        John Doe
        
        Experience:
        - Worked at company
        - Did some things
        
        Education:
        - Some degree
        """
        
        request_data = {
            'decision_slot_id': self.decision_slot_id,
            'resume_id': 'resume_test_001',
            'user_id': str(self.user.id),
            'resume_text': resume_text,
            'target_keywords': ['Python', 'Django', 'React', 'Leadership'],
            'include_recommendations': True,
            'include_ats_compatibility': True,
        }
        
        response = self.client.post(engine_url, request_data, format='json')
        
        # Step 2: Assert HTTP 200
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            f"Expected 200, got {response.status_code}. Response: {response.data}"
        )
        
        # Step 3: Assert response structure
        response_data = response.json()
        self.assertEqual(response_data['engine'], 'ResumeAuditEngine')
        self.assertEqual(response_data['contract_version'], '1.0.1')
        
        # Step 4: Assert engine output contains decision_slot_id
        engine_output = response_data['engine_output']
        self.assertEqual(engine_output['decision_slot_id'], self.decision_slot_id)
        
        # Step 5: Assert overall_score is a number
        self.assertIn('overall_score', engine_output)
        self.assertIsInstance(engine_output['overall_score'], (int, float))
        
        # Step 6: Assert trace metadata
        trace = response_data['trace']
        self.assertIn('latency_ms', trace)
        self.assertIsInstance(trace['latency_ms'], int)
        
        # Step 7: DB assertions - signals persisted
        persisted_signals = ATSSignal.objects.filter(decision_slot_id=self.decision_slot_id)
        self.assertGreater(
            persisted_signals.count(),
            0,
            "At least one signal should be persisted"
        )
        
        # Step 8: Verify all signals are anchored to decision_slot_id (Rule 15)
        for signal in persisted_signals:
            self.assertEqual(
                signal.decision_slot_id,
                self.decision_slot_id,
                f"Signal {signal.id} must be anchored to DecisionSlot {self.decision_slot_id} (Rule 15)"
            )
        
        # Step 9: If any signal is critical, verify human review task exists
        critical_signals = persisted_signals.filter(severity='critical')
        if critical_signals.exists():
            for critical_signal in critical_signals:
                review_tasks = HumanReviewTask.objects.filter(signal=critical_signal)
                self.assertGreater(
                    review_tasks.count(),
                    0,
                    f"HumanReviewTask should exist for critical signal {critical_signal.id}"
                )
                
                # Verify review task is anchored to same decision_slot_id
                for task in review_tasks:
                    self.assertEqual(
                        task.decision_slot_id,
                        self.decision_slot_id,
                        f"ReviewTask {task.id} must be anchored to DecisionSlot {self.decision_slot_id} (Rule 15)"
                    )
    
    def test_full_e2e_flow_without_critical_signal(self):
        """
        Test E2E flow when no critical signals are produced.
        
        Verifies that:
        - Signals are still persisted
        - No human review tasks are created (no critical signals)
        """
        engine_url = '/api/engines/signal-core/resume-audit/'
        
        # Resume text that should produce non-critical signals
        resume_text = """
        John Doe
        Email: john@example.com
        Phone: 555-1234
        
        Experience:
        - Senior Software Engineer at Tech Corp (2020-present)
          * Led team of 10 developers
          * Increased revenue by 50% using Python and Django
          * Implemented React frontend
        
        Skills:
        - Python, Django, React, JavaScript
        - Leadership, Communication, Agile
        
        Education:
        - Bachelor's in Computer Science, University of Technology (2016)
        """
        
        request_data = {
            'decision_slot_id': self.decision_slot_id,
            'resume_id': 'resume_test_002',
            'user_id': str(self.user.id),
            'resume_text': resume_text,
            'target_keywords': ['Python', 'Django', 'React'],
            'include_recommendations': True,
            'include_ats_compatibility': True,
        }
        
        response = self.client.post(engine_url, request_data, format='json')
        
        # Assert successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['engine'], 'ResumeAuditEngine')
        
        # Verify signals persisted
        persisted_signals = ATSSignal.objects.filter(decision_slot_id=self.decision_slot_id)
        self.assertGreater(persisted_signals.count(), 0)
        
        # Verify no critical signals -> no review tasks
        critical_signals = persisted_signals.filter(severity='critical')
        if critical_signals.count() == 0:
            review_tasks = HumanReviewTask.objects.filter(decision_slot_id=self.decision_slot_id)
            self.assertEqual(
                review_tasks.count(),
                0,
                "No review tasks should be created when there are no critical signals"
            )
    
    def test_engine_output_validation(self):
        """Test that engine output conforms to expected schema."""
        engine_url = '/api/engines/signal-core/resume-audit/'
        
        request_data = {
            'decision_slot_id': self.decision_slot_id,
            'resume_id': 'resume_test_003',
            'user_id': str(self.user.id),
            'resume_text': 'Minimal resume text for testing.',
        }
        
        response = self.client.post(engine_url, request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        
        # Verify required fields
        self.assertIn('engine', response_data)
        self.assertIn('contract_version', response_data)
        self.assertIn('engine_output', response_data)
        self.assertIn('trace', response_data)
        
        # Verify engine_output structure
        engine_output = response_data['engine_output']
        self.assertIn('decision_slot_id', engine_output)
        self.assertIn('overall_score', engine_output)
        self.assertIn('signals', engine_output)
        
        # Verify trace structure
        trace = response_data['trace']
        self.assertIn('latency_ms', trace)
        
        # Verify signals list
        signals = engine_output['signals']
        self.assertIsInstance(signals, list)
        
        # Verify signal structure (if any signals exist)
        if signals:
            signal = signals[0]
            self.assertIn('signal_type', signal)
            self.assertIn('severity', signal)
            self.assertIn('category', signal)
            self.assertIn('message', signal)

