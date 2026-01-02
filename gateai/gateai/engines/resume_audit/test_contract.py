"""
Contract tests for ResumeAuditEngine.

Tests schema enforcement, decision_slot anchoring, fallback logic, and traceability.
Conforms to ENGINE_RESUME_AUDIT.md specification and GateAI OS Contract v1.0.1.

Rule 14: AUTOMATED CONTRACT TESTING - All outputs MUST pass schema validation
Rule 15: SIGNAL INTEGRITY - All outputs MUST be anchored to DecisionSlot ID
"""

import pytest
from pydantic import ValidationError

from gateai.engines.resume_audit import ResumeAuditEngine
from gateai.engines.resume_audit.schemas import (
    ResumeAuditInput,
    ResumeAuditOutput,
    ResumeAuditSignal,
)


class TestResumeAuditEngineContract:
    """Contract tests for ResumeAuditEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing."""
        return ResumeAuditEngine()
    
    @pytest.fixture
    def minimal_valid_input(self):
        """Minimal valid input for testing."""
        return {
            'resume_id': 'resume_123',
            'resume_text': 'John Doe\nSoftware Engineer\n5 years of experience',
            'user_id': 'user_456',
        }
    
    @pytest.fixture
    def decision_slot_id(self):
        """Test decision slot ID."""
        return 'ds_test_123'
    
    def test_valid_input_produces_valid_output_schema(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that valid input produces output that conforms to ResumeAuditOutput schema.
        
        Rule 14: AUTOMATED CONTRACT TESTING
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        # Assert output is a dict
        assert isinstance(output, dict), "Output must be a dictionary"
        
        # Assert output conforms to schema (Rule 14)
        try:
            validated_output = engine.output_schema(**output)
            assert validated_output is not None, "Output schema validation must pass"
        except ValidationError as e:
            pytest.fail(f"Output does not conform to ResumeAuditOutput schema: {e}")
    
    def test_output_contains_decision_slot_id_and_matches(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that output contains decision_slot_id and it matches the input.
        
        Rule 15: SIGNAL INTEGRITY
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        # Assert decision_slot_id is present
        assert 'decision_slot_id' in output, "Output must contain decision_slot_id"
        
        # Assert decision_slot_id matches input (Rule 15)
        assert output['decision_slot_id'] == decision_slot_id, (
            f"Output decision_slot_id ({output['decision_slot_id']}) "
            f"must match input decision_slot_id ({decision_slot_id})"
        )
        
        # Assert decision_slot_id is non-empty string
        assert isinstance(output['decision_slot_id'], str), "decision_slot_id must be a string"
        assert len(output['decision_slot_id'].strip()) > 0, "decision_slot_id must be non-empty"
    
    def test_missing_required_fields_fails_input_validation(self, engine, minimal_valid_input):
        """
        Test that missing required fields causes input validation to fail.
        """
        # Test missing resume_text
        invalid_input = minimal_valid_input.copy()
        del invalid_input['resume_text']
        
        # Assert input validation fails
        assert not engine.validate_input(invalid_input), (
            "Input validation should fail when resume_text is missing"
        )
        
        # Test missing resume_id
        invalid_input = minimal_valid_input.copy()
        del invalid_input['resume_id']
        
        assert not engine.validate_input(invalid_input), (
            "Input validation should fail when resume_id is missing"
        )
        
        # Test missing user_id
        invalid_input = minimal_valid_input.copy()
        del invalid_input['user_id']
        
        assert not engine.validate_input(invalid_input), (
            "Input validation should fail when user_id is missing"
        )
    
    def test_empty_resume_text_fails_validation(self, engine, minimal_valid_input):
        """Test that empty resume_text fails validation."""
        invalid_input = minimal_valid_input.copy()
        invalid_input['resume_text'] = ''
        
        assert not engine.validate_input(invalid_input), (
            "Input validation should fail when resume_text is empty"
        )
    
    def test_invalid_decision_slot_id_raises_error(self, engine, minimal_valid_input):
        """
        Test that invalid decision_slot_id raises ValueError.
        
        Rule 15: SIGNAL INTEGRITY
        """
        # Test empty string
        with pytest.raises(ValueError, match="Invalid decision_slot_id"):
            engine.run(minimal_valid_input, "")
        
        # Test None
        with pytest.raises(ValueError, match="Invalid decision_slot_id"):
            engine.run(minimal_valid_input, None)
    
    def test_fallback_logic_returns_valid_output_schema(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that fallback_logic returns output that conforms to ResumeAuditOutput schema.
        
        Rule 7: Resilience
        Rule 14: AUTOMATED CONTRACT TESTING
        """
        # Create a test error
        test_error = Exception("Test error for fallback")
        
        # Call fallback_logic
        output = engine.fallback_logic(test_error, minimal_valid_input, decision_slot_id)
        
        # Assert output is a dict
        assert isinstance(output, dict), "Fallback output must be a dictionary"
        
        # Assert output conforms to schema (Rule 14)
        try:
            validated_output = engine.output_schema(**output)
            assert validated_output is not None, "Fallback output schema validation must pass"
        except ValidationError as e:
            pytest.fail(f"Fallback output does not conform to ResumeAuditOutput schema: {e}")
        
        # Assert decision_slot_id is present and matches (Rule 15)
        assert output['decision_slot_id'] == decision_slot_id, (
            "Fallback output must anchor to decision_slot_id"
        )
        
        # Assert fallback output indicates failure
        assert output['overall_score'] == 0.0, "Fallback output should have score of 0.0"
        assert output['score_category'] == 'poor', "Fallback output should have score_category 'poor'"
        assert output['confidence_score'] == 0.0, "Fallback output should have confidence_score of 0.0"
        
        # Assert error signal is present
        assert len(output['signals']) > 0, "Fallback output should contain error signal"
        error_signal = output['signals'][0]
        assert error_signal['signal_type'] == 'structure_issue', "Error signal should be structure_issue"
        assert error_signal['severity'] == 'critical', "Error signal should be critical"
    
    def test_trace_metadata_shape(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that trace_metadata returns correct shape.
        
        Rule 9: Cost Awareness
        Rule 10: Traceability
        """
        # Execute engine to generate trace
        engine.run(minimal_valid_input, decision_slot_id)
        
        # Get trace metadata
        trace = engine.trace_metadata()
        
        # Assert trace is a dict
        assert isinstance(trace, dict), "Trace metadata must be a dictionary"
        
        # Assert required fields are present
        assert 'latency_ms' in trace, "Trace metadata must contain latency_ms"
        assert 'tokens_used' in trace, "Trace metadata must contain tokens_used"
        assert 'model_version' in trace, "Trace metadata must contain model_version"
        
        # Assert latency_ms is int and non-negative
        assert isinstance(trace['latency_ms'], int), "latency_ms must be an integer"
        assert trace['latency_ms'] >= 0, "latency_ms must be non-negative"
        
        # Assert tokens_used is None (no LLM calls)
        assert trace['tokens_used'] is None, "tokens_used must be None (no LLM calls)"
        
        # Assert model_version is None (no LLM calls)
        assert trace['model_version'] is None, "model_version must be None (no LLM calls)"
    
    def test_signal_types_are_within_allowed_set(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that all generated signals have valid signal types.
        
        Optional test for signal type validation.
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        # Get allowed signal types
        allowed_types = {
            'structure_issue',
            'content_issue',
            'keyword_missing',
            'ats_incompatibility',
            'skill_gap',
            'formatting_issue',
            'strength',
            'recommendation',
        }
        
        # Assert all signals have valid types
        for signal in output['signals']:
            assert signal['signal_type'] in allowed_types, (
                f"Signal type '{signal['signal_type']}' is not in allowed set: {allowed_types}"
            )
    
    def test_severity_is_in_allowed_set(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that all generated signals have valid severity levels.
        
        Optional test for severity validation.
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        # Get allowed severity levels
        allowed_severities = {'critical', 'high', 'medium', 'low', 'info'}
        
        # Assert all signals have valid severities
        for signal in output['signals']:
            assert signal['severity'] in allowed_severities, (
                f"Signal severity '{signal['severity']}' is not in allowed set: {allowed_severities}"
            )
    
    def test_output_scores_are_within_valid_range(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that all scores in output are within valid range (0-100).
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        # Assert score ranges
        assert 0.0 <= output['overall_score'] <= 100.0, "overall_score must be between 0 and 100"
        assert 0.0 <= output['structure_score'] <= 100.0, "structure_score must be between 0 and 100"
        assert 0.0 <= output['content_score'] <= 100.0, "content_score must be between 0 and 100"
        assert 0.0 <= output['keyword_score'] <= 100.0, "keyword_score must be between 0 and 100"
        
        if output['ats_compatibility_score'] is not None:
            assert 0.0 <= output['ats_compatibility_score'] <= 100.0, (
                "ats_compatibility_score must be between 0 and 100"
            )
        
        # Assert confidence_score is between 0 and 1
        assert 0.0 <= output['confidence_score'] <= 1.0, "confidence_score must be between 0 and 1"
    
    def test_score_category_matches_overall_score(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that score_category correctly matches overall_score range.
        """
        # Execute engine
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        score = output['overall_score']
        category = output['score_category']
        
        # Assert category matches score range
        if score >= 90:
            assert category == 'excellent', f"Score {score} should be 'excellent'"
        elif score >= 80:
            assert category == 'good', f"Score {score} should be 'good'"
        elif score >= 70:
            assert category == 'fair', f"Score {score} should be 'fair'"
        elif score >= 60:
            assert category == 'needs_improvement', f"Score {score} should be 'needs_improvement'"
        else:
            assert category == 'poor', f"Score {score} should be 'poor'"
    
    def test_engine_version_is_present(self, engine, minimal_valid_input, decision_slot_id):
        """Test that engine_version is present in output."""
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        assert 'engine_version' in output, "Output must contain engine_version"
        assert isinstance(output['engine_version'], str), "engine_version must be a string"
        assert len(output['engine_version']) > 0, "engine_version must be non-empty"
    
    def test_timestamp_is_present(self, engine, minimal_valid_input, decision_slot_id):
        """Test that timestamp is present in output."""
        from datetime import datetime
        
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        assert 'timestamp' in output, "Output must contain timestamp"
        # Timestamp should be a datetime object or ISO string
        assert output['timestamp'] is not None, "timestamp must not be None"
    
    def test_processing_time_is_non_negative(self, engine, minimal_valid_input, decision_slot_id):
        """Test that processing_time_seconds is non-negative."""
        output = engine.run(minimal_valid_input, decision_slot_id)
        
        assert 'processing_time_seconds' in output, "Output must contain processing_time_seconds"
        assert isinstance(output['processing_time_seconds'], (int, float)), (
            "processing_time_seconds must be a number"
        )
        assert output['processing_time_seconds'] >= 0.0, (
            "processing_time_seconds must be non-negative"
        )
    
    def test_fallback_preserves_decision_slot_id(self, engine, minimal_valid_input, decision_slot_id):
        """
        Test that fallback_logic preserves decision_slot_id even on error.
        
        Rule 15: SIGNAL INTEGRITY
        """
        test_error = Exception("Test error")
        output = engine.fallback_logic(test_error, minimal_valid_input, decision_slot_id)
        
        assert output['decision_slot_id'] == decision_slot_id, (
            "Fallback must preserve decision_slot_id (Rule 15)"
        )
    
    def test_comprehensive_input_with_all_fields(self, engine, decision_slot_id):
        """Test engine with comprehensive input including all optional fields."""
        comprehensive_input = {
            'resume_id': 'resume_789',
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
            'user_id': 'user_999',
            'target_job_title': 'Senior Software Engineer',
            'target_industry': 'Technology',
            'target_keywords': ['Python', 'React', 'Leadership'],
            'analysis_depth': 'comprehensive',
            'include_recommendations': True,
            'include_ats_compatibility': True,
            'resume_file_type': 'pdf',
            'resume_file_size': 50000,
        }
        
        # Execute engine
        output = engine.run(comprehensive_input, decision_slot_id)
        
        # Assert output is valid
        assert engine.validate_output(output), "Comprehensive input should produce valid output"
        assert output['decision_slot_id'] == decision_slot_id, "Decision slot ID must match"
        
        # Assert recommendations are included
        assert output['recommendations'] is not None, "Recommendations should be included"
        
        # Assert ATS score is included
        assert output['ats_compatibility_score'] is not None, "ATS score should be included"

