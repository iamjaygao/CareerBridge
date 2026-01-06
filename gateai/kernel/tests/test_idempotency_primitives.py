"""
Tests for kernel idempotency primitives - atomic claim operations.
"""

import uuid
from django.test import TestCase, TransactionTestCase

from kernel.idempotency_primitives import claim_idempotency_key, mark_key_failed
from kernel.models import KernelIdempotencyRecord


class IdempotencyClaimTestCase(TransactionTestCase):
    """
    Test atomic idempotency key claiming.
    
    Uses TransactionTestCase to ensure proper transaction isolation testing.
    """
    
    def test_claim_new_key_succeeds(self):
        """First claim of a new key should succeed."""
        key = f"test-key-{uuid.uuid4()}"
        event_id = str(uuid.uuid4())
        
        claimed, record = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id,
        )
        
        self.assertTrue(claimed, "First claim should succeed")
        self.assertEqual(record.idempotency_key, key)
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_PROCESSED)
        self.assertEqual(str(record.last_event_id), event_id)
    
    def test_claim_existing_key_rejected_no_exception(self):
        """Second claim of same key should be rejected cleanly without exceptions."""
        key = f"test-key-{uuid.uuid4()}"
        event_id_1 = str(uuid.uuid4())
        event_id_2 = str(uuid.uuid4())
        
        # First claim
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id_1,
        )
        self.assertTrue(claimed1, "First claim should succeed")
        
        # Second claim (replay)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id_2,
        )
        
        self.assertFalse(claimed2, "Second claim should be rejected")
        self.assertEqual(record2.idempotency_key, key)
        self.assertEqual(str(record2.last_event_id), event_id_1, "Should return original record")
    
    def test_concurrent_claim_deterministic(self):
        """
        Simulate race condition with sequential claims.
        
        Both claims should complete without exceptions, and exactly one should succeed.
        """
        key = f"test-key-{uuid.uuid4()}"
        
        # Claim 1
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=str(uuid.uuid4()),
        )
        
        # Claim 2 (simulated race)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=str(uuid.uuid4()),
        )
        
        # Exactly one should have claimed
        self.assertTrue(claimed1, "First claim should succeed")
        self.assertFalse(claimed2, "Second claim should fail")
        
        # Both should return valid records
        self.assertIsNotNone(record1)
        self.assertIsNotNone(record2)
        
        # Both should refer to the same underlying key
        self.assertEqual(record1.idempotency_key, record2.idempotency_key)
    
    def test_mark_key_failed(self):
        """Test marking a key as failed."""
        key = f"test-key-{uuid.uuid4()}"
        
        # Create a key
        claimed, record = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
        )
        self.assertTrue(claimed)
        
        # Mark as failed
        success = mark_key_failed(key, "Test failure reason")
        self.assertTrue(success)
        
        # Verify status updated
        record.refresh_from_db()
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_FAILED)
        self.assertEqual(record.failure_reason, "Test failure reason")
    
    def test_mark_nonexistent_key_failed_returns_false(self):
        """Marking a non-existent key as failed should return False gracefully."""
        success = mark_key_failed("nonexistent-key", "Test")
        self.assertFalse(success)


class StateTransitionTestCase(TestCase):
    """Test monotonic state machine for KernelAuditLog and KernelIdempotencyRecord."""
    
    def test_audit_log_terminal_state_blocks_transition(self):
        """KernelAuditLog: HANDLED cannot transition to FAILED."""
        from kernel.models import KernelAuditLog
        
        # Valid transitions
        self.assertTrue(KernelAuditLog.is_valid_transition("EMITTED", "HANDLED"))
        self.assertTrue(KernelAuditLog.is_valid_transition("EMITTED", "FAILED"))
        self.assertTrue(KernelAuditLog.is_valid_transition("EMITTED", "REJECTED"))
        
        # Terminal state cannot transition
        self.assertFalse(KernelAuditLog.is_valid_transition("HANDLED", "FAILED"))
        self.assertFalse(KernelAuditLog.is_valid_transition("REJECTED", "FAILED"))
        self.assertFalse(KernelAuditLog.is_valid_transition("REJECTED", "HANDLED"))
        
        # Idempotent updates allowed (same status)
        self.assertTrue(KernelAuditLog.is_valid_transition("HANDLED", "HANDLED"))
        self.assertTrue(KernelAuditLog.is_valid_transition("REJECTED", "REJECTED"))
    
    def test_idempotency_record_terminal_state_blocks_failed(self):
        """KernelIdempotencyRecord: PROCESSED/REJECTED cannot transition to FAILED."""
        from kernel.models import KernelIdempotencyRecord
        
        # Valid transitions
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("FAILED", "PROCESSED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("FAILED", "REJECTED"))
        
        # Terminal states cannot transition to FAILED
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("PROCESSED", "FAILED"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("REJECTED", "FAILED"))
        
        # Idempotent updates allowed
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("PROCESSED", "PROCESSED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("REJECTED", "REJECTED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("FAILED", "FAILED"))
    
    def test_safe_mark_handled_respects_transitions(self):
        """safe_mark_handled should reject invalid state transitions."""
        from kernel.models import KernelAuditLog
        import uuid
        
        # Create event in terminal state
        event = KernelAuditLog.objects.create(
            event_type="TEST_EVENT",
            decision_id="test-1",
            idempotency_key="test-key-1",
            context_hash="abc123",
            status=KernelAuditLog.STATUS_HANDLED,
        )
        
        # Try to transition to FAILED (should be blocked)
        result = KernelAuditLog.safe_mark_handled(
            event.event_id,
            status=KernelAuditLog.STATUS_FAILED,
            failure_reason="Should not work",
        )
        
        self.assertFalse(result, "Transition from HANDLED to FAILED should be blocked")
        
        # Verify status unchanged
        event.refresh_from_db()
        self.assertEqual(event.status, KernelAuditLog.STATUS_HANDLED)
        self.assertEqual(event.failure_reason, "")  # Should not be updated

