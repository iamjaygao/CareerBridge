"""
Tests for kernel lock primitives - stateless helpers.
"""

from django.test import TestCase
from django.utils import timezone

from kernel.lock_primitives import compute_lock_release_audit


class LockPrimitivesTestCase(TestCase):
    """Test stateless lock release audit computation."""
    
    def test_compute_full_release_audit(self):
        """Full release (no resource specifics) should be marked as FULL."""
        result = compute_lock_release_audit(
            decision_id="test-decision-1",
            reason="Testing full release",
        )
        
        self.assertEqual(result["decision_id"], "test-decision-1")
        self.assertEqual(result["release_type"], "FULL")
        self.assertEqual(result["reason"], "Testing full release")
        self.assertIn("released_at", result)
        self.assertNotIn("resource_type", result)
        self.assertNotIn("resource_id", result)
    
    def test_compute_partial_release_audit(self):
        """Partial release (with resource specifics) should be marked as PARTIAL."""
        result = compute_lock_release_audit(
            decision_id="test-decision-2",
            resource_type="APPOINTMENT",
            resource_id=123,
            resource_key="slot-456",
            reason="Testing partial release",
        )
        
        self.assertEqual(result["decision_id"], "test-decision-2")
        self.assertEqual(result["release_type"], "PARTIAL")
        self.assertEqual(result["resource_type"], "APPOINTMENT")
        self.assertEqual(result["resource_id"], "123")
        self.assertEqual(result["resource_key"], "slot-456")
        self.assertEqual(result["reason"], "Testing partial release")
        self.assertIn("released_at", result)
    
    def test_compute_audit_no_reason(self):
        """Audit payload should be valid even without reason."""
        result = compute_lock_release_audit(
            decision_id="test-decision-3",
        )
        
        self.assertEqual(result["decision_id"], "test-decision-3")
        self.assertEqual(result["release_type"], "FULL")
        self.assertIn("released_at", result)
        self.assertNotIn("reason", result)
    
    def test_compute_audit_stable_keys(self):
        """Result should always have predictable keys."""
        result = compute_lock_release_audit(
            decision_id="test",
            resource_type="TEST",
            resource_id=1,
        )
        
        required_keys = {"decision_id", "released_at", "release_type"}
        self.assertTrue(required_keys.issubset(result.keys()))
    
    def test_released_at_is_iso_string(self):
        """released_at should be ISO format string."""
        result = compute_lock_release_audit(decision_id="test")
        
        released_at = result["released_at"]
        self.assertIsInstance(released_at, str)
        
        # Should be parseable as ISO datetime
        from datetime import datetime
        parsed = datetime.fromisoformat(released_at.replace("Z", "+00:00"))
        self.assertIsNotNone(parsed)

