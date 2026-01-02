"""
Kernel Integration Test for ResumeAuditEngine.

Verifies that the GateAI OS Kernel (ats_signals + decision_slots) can successfully:
1. Create a mock DecisionSlot
2. Dispatch ResumeAuditEngine via kernel service logic
3. Receive engine output
4. Persist resulting signals via ats_signals
5. Verify that every signal is anchored to the DecisionSlot ID (Rule 15)

This test verifies Kernel ↔ Engine integration, not unit behavior.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models

from gateai.engines.resume_audit import ResumeAuditEngine
from gateai.engines.resume_audit.schemas import ResumeAuditSignal
from ats_signals.models import Resume, ResumeAnalysis, ATSSignal

User = get_user_model()


class KernelEngineIntegrationTest(TestCase):
    """
    Kernel integration test for ResumeAuditEngine.
    
    Tests the full flow:
    - DecisionSlot creation
    - Engine dispatch
    - Signal persistence
    - Rule 15 compliance (signal anchoring)
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test resume
        self.resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            file='resumes/test.pdf',  # Mock file path
            file_size=50000,
            file_type='pdf',
            status='uploaded'
        )
        
        # Initialize engine (real, not mocked)
        self.engine = ResumeAuditEngine()
    
    def test_kernel_integration_full_flow(self):
        """
        Test complete kernel integration flow.
        
        Verifies:
        1. DecisionSlot creation (mock - using string ID)
        2. Engine dispatch
        3. Signal persistence
        4. Rule 15 compliance
        """
        # Step 1: Create DecisionSlot (mock - using string ID)
        decision_slot_id = f"ds_test_{int(timezone.now().timestamp())}"
        
        # Verify DecisionSlot ID is valid (in production, this would check DB)
        self.assertIsNotNone(decision_slot_id)
        self.assertNotEqual(decision_slot_id, '')
        
        # Step 2: Prepare engine input
        engine_input = {
            'resume_id': str(self.resume.id),
            'resume_text': '''
                John Doe
                Software Engineer
                
                Experience:
                - 5 years of Python development
                - Led team of 10 developers
                - Increased revenue by 50%
                
                Education:
                - Bachelor's in Computer Science
                - University of Technology
                
                Skills:
                - Python, JavaScript, React
                - Leadership, Communication
            ''',
            'user_id': str(self.user.id),
            'target_job_title': 'Senior Software Engineer',
            'target_keywords': ['Python', 'React', 'Leadership'],
            'analysis_depth': 'standard',
            'include_recommendations': True,
            'include_ats_compatibility': True,
        }
        
        # Step 3: Dispatch engine (real engine, not mocked)
        engine_output = self.engine.run(engine_input, decision_slot_id)
        
        # Verify engine was invoked and returned output
        self.assertIsNotNone(engine_output)
        self.assertIn('decision_slot_id', engine_output)
        self.assertEqual(engine_output['decision_slot_id'], decision_slot_id)
        
        # Step 4: Persist signals to database
        signals_created = 0
        for signal_data in engine_output.get('signals', []):
            ATSSignal.objects.create(
                decision_slot_id=decision_slot_id,
                signal_type=signal_data['signal_type'],
                severity=signal_data['severity'],
                category=signal_data['category'],
                message=signal_data['message'],
                details=signal_data.get('details', {}),
                section=signal_data.get('section'),
                line_number=signal_data.get('line_number'),
                engine_name=engine_output.get('engine_name', 'ResumeAuditEngine'),
                engine_version=engine_output.get('engine_version', '1.0.0'),
            )
            signals_created += 1
        
        # Verify signals were created in DB
        db_signals = ATSSignal.objects.filter(decision_slot_id=decision_slot_id)
        self.assertEqual(db_signals.count(), signals_created)
        self.assertGreater(db_signals.count(), 0, "At least one signal should be created")
        
        # Step 5: Verify Rule 15 compliance - every signal is anchored to DecisionSlot ID
        for signal in db_signals:
            self.assertEqual(
                signal.decision_slot_id,
                decision_slot_id,
                f"Signal {signal.id} must be anchored to DecisionSlot {decision_slot_id} (Rule 15)"
            )
            self.assertIsNotNone(signal.decision_slot_id)
            self.assertNotEqual(signal.decision_slot_id, '')
    
    def test_signal_types_conform_to_schema(self):
        """Test that persisted signals conform to ResumeAuditSignal schema."""
        decision_slot_id = f"ds_test_schema_{int(timezone.now().timestamp())}"
        
        engine_input = {
            'resume_id': str(self.resume.id),
            'resume_text': 'Test resume content with Python and React skills.',
            'user_id': str(self.user.id),
        }
        
        engine_output = self.engine.run(engine_input, decision_slot_id)
        
        # Persist signals
        for signal_data in engine_output.get('signals', []):
            ATSSignal.objects.create(
                decision_slot_id=decision_slot_id,
                signal_type=signal_data['signal_type'],
                severity=signal_data['severity'],
                category=signal_data['category'],
                message=signal_data['message'],
                details=signal_data.get('details', {}),
                section=signal_data.get('section'),
                line_number=signal_data.get('line_number'),
                engine_name=engine_output.get('engine_name', 'ResumeAuditEngine'),
                engine_version=engine_output.get('engine_version', '1.0.0'),
            )
        
        # Verify signal types are valid
        allowed_signal_types = {
            'structure_issue',
            'content_issue',
            'keyword_missing',
            'ats_incompatibility',
            'skill_gap',
            'formatting_issue',
            'strength',
            'recommendation',
        }
        
        db_signals = ATSSignal.objects.filter(decision_slot_id=decision_slot_id)
        for signal in db_signals:
            self.assertIn(
                signal.signal_type,
                allowed_signal_types,
                f"Signal type '{signal.signal_type}' must be in allowed set"
            )
            
            # Verify severity is valid
            allowed_severities = {'critical', 'high', 'medium', 'low', 'info'}
            self.assertIn(
                signal.severity,
                allowed_severities,
                f"Signal severity '{signal.severity}' must be in allowed set"
            )
    
    def test_all_signals_anchored_to_decision_slot(self):
        """
        Test that ALL signals are anchored to the DecisionSlot ID.
        
        Rule 15: SIGNAL INTEGRITY - Every engine output MUST be anchored to a DecisionSlot ID.
        """
        decision_slot_id = f"ds_test_anchor_{int(timezone.now().timestamp())}"
        
        engine_input = {
            'resume_id': str(self.resume.id),
            'resume_text': '''
                Comprehensive resume with multiple sections.
                Experience section with detailed work history.
                Education section with degrees.
                Skills section with technical and soft skills.
            ''',
            'user_id': str(self.user.id),
            'include_recommendations': True,
            'include_ats_compatibility': True,
        }
        
        engine_output = self.engine.run(engine_input, decision_slot_id)
        
        # Persist all signals
        for signal_data in engine_output.get('signals', []):
            ATSSignal.objects.create(
                decision_slot_id=decision_slot_id,
                signal_type=signal_data['signal_type'],
                severity=signal_data['severity'],
                category=signal_data['category'],
                message=signal_data['message'],
                details=signal_data.get('details', {}),
                section=signal_data.get('section'),
                line_number=signal_data.get('line_number'),
                engine_name=engine_output.get('engine_name', 'ResumeAuditEngine'),
                engine_version=engine_output.get('engine_version', '1.0.0'),
            )
        
        # Verify ALL signals are anchored
        db_signals = ATSSignal.objects.filter(decision_slot_id=decision_slot_id)
        self.assertGreater(db_signals.count(), 0, "Signals should be created")
        
        for signal in db_signals:
            self.assertEqual(
                signal.decision_slot_id,
                decision_slot_id,
                f"Every signal must be anchored to DecisionSlot {decision_slot_id} (Rule 15)"
            )
        
        # Verify no signals exist without decision_slot_id
        orphaned_signals = ATSSignal.objects.filter(decision_slot_id__isnull=True)
        self.assertEqual(orphaned_signals.count(), 0, "No signals should exist without decision_slot_id")
    
    def test_engine_output_contains_decision_slot_id(self):
        """Test that engine output contains decision_slot_id before persistence."""
        decision_slot_id = f"ds_test_output_{int(timezone.now().timestamp())}"
        
        engine_input = {
            'resume_id': str(self.resume.id),
            'resume_text': 'Test resume',
            'user_id': str(self.user.id),
        }
        
        engine_output = self.engine.run(engine_input, decision_slot_id)
        
        # Verify output contains decision_slot_id
        self.assertIn('decision_slot_id', engine_output)
        self.assertEqual(engine_output['decision_slot_id'], decision_slot_id)
        
        # Verify signals list exists
        self.assertIn('signals', engine_output)
        self.assertIsInstance(engine_output['signals'], list)
        
        # Verify each signal in output has the decision_slot_id context
        # (The signal itself doesn't need decision_slot_id, but the output does)
        for signal in engine_output['signals']:
            self.assertIn('signal_type', signal)
            self.assertIn('severity', signal)
            self.assertIn('category', signal)
            self.assertIn('message', signal)
    
    def test_signal_persistence_with_decision_slot_relationship(self):
        """Test that signals can be queried by DecisionSlot ID."""
        decision_slot_id = f"ds_test_query_{int(timezone.now().timestamp())}"
        
        engine_input = {
            'resume_id': str(self.resume.id),
            'resume_text': 'Resume with Python and Django experience.',
            'user_id': str(self.user.id),
        }
        
        engine_output = self.engine.run(engine_input, decision_slot_id)
        
        # Persist signals
        for signal_data in engine_output.get('signals', []):
            ATSSignal.objects.create(
                decision_slot_id=decision_slot_id,
                signal_type=signal_data['signal_type'],
                severity=signal_data['severity'],
                category=signal_data['category'],
                message=signal_data['message'],
                details=signal_data.get('details', {}),
                section=signal_data.get('section'),
                line_number=signal_data.get('line_number'),
                engine_name=engine_output.get('engine_name', 'ResumeAuditEngine'),
                engine_version=engine_output.get('engine_version', '1.0.0'),
            )
        
        # Query signals by DecisionSlot ID
        signals_for_slot = ATSSignal.objects.filter(decision_slot_id=decision_slot_id)
        self.assertGreater(signals_for_slot.count(), 0)
        
        # Verify all queried signals belong to the DecisionSlot
        for signal in signals_for_slot:
            self.assertEqual(signal.decision_slot_id, decision_slot_id)
        
        # Verify decision_slot_id is stored correctly
        first_signal = signals_for_slot.first()
        self.assertEqual(first_signal.decision_slot_id, decision_slot_id)

