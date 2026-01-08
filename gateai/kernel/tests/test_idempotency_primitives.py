"""
Tests for kernel idempotency primitives - atomic claim operations.
"""

import uuid
from django.test import TestCase, TransactionTestCase

from kernel.idempotency_primitives import (
    claim_idempotency_key,
    mark_key_failed,
    mark_key_succeeded,
)
from kernel.models import KernelIdempotencyRecord


class IdempotencyClaimTestCase(TransactionTestCase):
    """
    Test atomic idempotency key claiming.
    
    Uses TransactionTestCase to ensure proper transaction isolation testing.
    """
    
    def test_claim_new_key_succeeds(self):
        """First claim of a new key should succeed with IN_PROGRESS status."""
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
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_IN_PROGRESS)
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
    
    def test_transient_failure_after_claim_no_false_replay(self):
        """
        CRITICAL: Transient failure after claim must NOT cause false REPLAY.
        
        Scenario:
        1. First request claims key (status=IN_PROGRESS)
        2. Request fails before marking SUCCEEDED
        3. Second request must NOT treat this as successful replay
        
        Expected: Second request gets claimed=False with status=IN_PROGRESS (not SUCCESS)
        """
        key = f"test-key-{uuid.uuid4()}"
        event_id_1 = str(uuid.uuid4())
        event_id_2 = str(uuid.uuid4())
        
        # First claim succeeds
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id_1,
        )
        self.assertTrue(claimed1, "First claim should succeed")
        self.assertEqual(record1.status, KernelIdempotencyRecord.STATUS_IN_PROGRESS)
        
        # Simulate transient failure: operation fails before marking succeeded
        # (No call to mark_key_succeeded)
        
        # Second request (retry or duplicate)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id_2,
        )
        
        # CRITICAL ASSERTION: claimed=False but status is NOT a success state
        self.assertFalse(claimed2, "Second claim should be rejected")
        self.assertEqual(record2.status, KernelIdempotencyRecord.STATUS_IN_PROGRESS)
        self.assertNotIn(
            record2.status,
            KernelIdempotencyRecord.SUCCESS_STATES,
            "Status must NOT be in SUCCESS_STATES (operation never completed)",
        )
        
        # Caller MUST NOT treat this as successful replay
        # Caller should detect IN_PROGRESS and either fail or retry
    
    def test_succeeded_status_allows_safe_replay(self):
        """
        REPLAY is only safe when status=SUCCEEDED.
        
        Scenario:
        1. First request claims key and succeeds (status=SUCCEEDED)
        2. Second request gets claimed=False with status=SUCCEEDED
        3. Caller can safely treat as REPLAY of completed operation
        """
        key = f"test-key-{uuid.uuid4()}"
        event_id = str(uuid.uuid4())
        
        # First claim succeeds
        claimed, record = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=event_id,
        )
        self.assertTrue(claimed)
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_IN_PROGRESS)
        
        # Mark as succeeded (operation completed successfully)
        success = mark_key_succeeded(key, event_id)
        self.assertTrue(success)
        
        # Second request (replay)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=str(uuid.uuid4()),
        )
        
        # SAFE REPLAY: claimed=False AND status in SUCCESS_STATES
        self.assertFalse(claimed2, "Second claim should be rejected")
        self.assertEqual(record2.status, KernelIdempotencyRecord.STATUS_SUCCEEDED)
        self.assertIn(
            record2.status,
            KernelIdempotencyRecord.SUCCESS_STATES,
            "Status must be in SUCCESS_STATES for safe replay",
        )
        
        # Caller can safely return cached result or no-op
    
    def test_idempotency_key_collision_semantic_mismatch(self):
        """
        CRITICAL: Detect idempotency key collision (same key, different operation).
        
        Scenario:
        1. First request claims key with context_hash="abc123"
        2. Second request uses SAME key but DIFFERENT context_hash="xyz789"
        3. This is a deterministic CONFLICT (not a replay)
        
        Expected: Second request gets claimed=False with failure_reason=IDEMPOTENCY_KEY_COLLISION
        """
        key = f"test-key-{uuid.uuid4()}"
        
        # First claim
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
            event_id=str(uuid.uuid4()),
        )
        self.assertTrue(claimed1, "First claim should succeed")
        
        # Second claim with DIFFERENT context_hash (semantic collision)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="xyz789",  # DIFFERENT
            event_id=str(uuid.uuid4()),
        )
        
        # COLLISION DETECTED
        self.assertFalse(claimed2, "Second claim should be rejected")
        self.assertEqual(record2.failure_reason, "IDEMPOTENCY_KEY_COLLISION")
        
        # Original record should still have original context_hash
        record1.refresh_from_db()
        self.assertEqual(record1.context_hash, "abc123", "Original context_hash must be preserved")
    
    def test_idempotency_key_collision_event_type_mismatch(self):
        """Test collision detection with different event_type."""
        key = f"test-key-{uuid.uuid4()}"
        
        # First claim
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT_A",
            decision_id="test-decision-1",
            context_hash="abc123",
            owner_id="owner1",
        )
        self.assertTrue(claimed1)
        
        # Second claim with DIFFERENT event_type (collision)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT_B",  # DIFFERENT
            decision_id="test-decision-1",
            context_hash="abc123",
            owner_id="owner1",
        )
        
        # COLLISION DETECTED
        self.assertFalse(claimed2)
        self.assertEqual(record2.failure_reason, "IDEMPOTENCY_KEY_COLLISION")
    
    def test_idempotency_key_collision_owner_id_mismatch(self):
        """Test collision detection with different owner_id (semantic identity)."""
        key = f"test-key-{uuid.uuid4()}"
        
        # First claim
        claimed1, record1 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="decision-A",
            context_hash="abc123",
            owner_id="owner-A",
        )
        self.assertTrue(claimed1)
        
        # Second claim with DIFFERENT owner_id (collision)
        # Note: decision_id can differ (not part of semantic identity)
        claimed2, record2 = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="decision-B",  # Can differ (not semantic identity)
            context_hash="abc123",  # Same
            owner_id="owner-B",  # DIFFERENT - collision!
        )
        
        # COLLISION DETECTED (different owner_id = different semantic identity)
        self.assertFalse(claimed2)
        self.assertEqual(record2.failure_reason, "IDEMPOTENCY_KEY_COLLISION")
    
    def test_mark_key_failed_only_from_in_progress(self):
        """mark_key_failed should only transition from IN_PROGRESS, not from terminal states."""
        key = f"test-key-{uuid.uuid4()}"
        
        # Create key and mark as succeeded
        claimed, record = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
        )
        self.assertTrue(claimed)
        mark_key_succeeded(key)
        
        # Try to mark as failed (should be blocked)
        result = mark_key_failed(key, "Should not work")
        self.assertFalse(result, "Cannot transition from SUCCEEDED to FAILED")
        
        # Verify status unchanged
        record.refresh_from_db()
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_SUCCEEDED)
        self.assertNotEqual(record.failure_reason, "Should not work")
    
    def test_mark_key_succeeded_only_from_in_progress(self):
        """mark_key_succeeded should validate state transitions."""
        key = f"test-key-{uuid.uuid4()}"
        
        # Create key in IN_PROGRESS
        claimed, record = claim_idempotency_key(
            idempotency_key=key,
            event_type="TEST_EVENT",
            decision_id="test-decision-1",
            context_hash="abc123",
        )
        self.assertTrue(claimed)
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_IN_PROGRESS)
        
        # Mark as succeeded (valid transition)
        result = mark_key_succeeded(key)
        self.assertTrue(result)
        
        # Verify status updated
        record.refresh_from_db()
        self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_SUCCEEDED)
        
        # Try to mark as succeeded again (idempotent, should succeed)
        result2 = mark_key_succeeded(key)
        self.assertTrue(result2, "Idempotent SUCCEEDED -> SUCCEEDED should be allowed")


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
        """KernelIdempotencyRecord: Terminal states cannot transition to any other state."""
        from kernel.models import KernelIdempotencyRecord
        
        # Valid transitions from non-terminal states
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("IN_PROGRESS", "SUCCEEDED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("IN_PROGRESS", "FAILED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("IN_PROGRESS", "REJECTED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("FAILED", "SUCCEEDED"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("FAILED", "IN_PROGRESS"))
        
        # Terminal states cannot transition to any other state
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("SUCCEEDED", "FAILED"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("SUCCEEDED", "IN_PROGRESS"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("PROCESSED", "FAILED"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("PROCESSED", "IN_PROGRESS"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("REJECTED", "FAILED"))
        self.assertFalse(KernelIdempotencyRecord.is_valid_transition("REJECTED", "IN_PROGRESS"))
        
        # Idempotent updates allowed (same status)
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("IN_PROGRESS", "IN_PROGRESS"))
        self.assertTrue(KernelIdempotencyRecord.is_valid_transition("SUCCEEDED", "SUCCEEDED"))
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

