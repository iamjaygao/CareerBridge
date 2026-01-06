"""
Tests for ResourceLock release logic - physical delete + re-lockability.
"""

from django.test import TransactionTestCase
from django.utils import timezone
from datetime import timedelta

from decision_slots.models import ResourceLock
from kernel.models import KernelAuditLog


class ResourceLockReleaseTestCase(TransactionTestCase):
    """Test lock release with physical delete and re-locking."""
    
    def setUp(self):
        """Set up test data."""
        self.expires_at = timezone.now() + timedelta(hours=1)
    
    def test_full_release_deletes_all_locks(self):
        """release_for_decision should physically delete all locks for a decision."""
        # Create multiple locks for same decision
        ResourceLock.create_lock(
            decision_id="test-decision-1",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
            owner_id=1,
            expires_at=self.expires_at,
        )
        ResourceLock.create_lock(
            decision_id="test-decision-1",
            resource_type=ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            resource_id=200,
            owner_id=1,
            expires_at=self.expires_at,
        )
        
        # Verify locks exist
        self.assertEqual(ResourceLock.objects.filter(decision_id="test-decision-1").count(), 2)
        
        # Release all locks
        count = ResourceLock.release_for_decision("test-decision-1", reason="Test full release")
        
        self.assertEqual(count, 2)
        self.assertEqual(ResourceLock.objects.filter(decision_id="test-decision-1").count(), 0)
        
        # Verify audit entries created
        audit_entries = KernelAuditLog.objects.filter(
            event_type="RESOURCE_LOCK_RELEASED",
            decision_id="test-decision-1"
        )
        self.assertEqual(audit_entries.count(), 2)
    
    def test_partial_release_deletes_specific_lock(self):
        """release_specific should only delete the targeted lock."""
        # Create multiple locks for same decision
        ResourceLock.create_lock(
            decision_id="test-decision-2",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
            owner_id=1,
            expires_at=self.expires_at,
        )
        ResourceLock.create_lock(
            decision_id="test-decision-2",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=200,
            owner_id=1,
            expires_at=self.expires_at,
        )
        
        # Release specific lock
        success = ResourceLock.release_specific(
            decision_id="test-decision-2",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
            reason="Test partial release",
        )
        
        self.assertTrue(success)
        
        # Verify only one lock deleted
        remaining = ResourceLock.objects.filter(decision_id="test-decision-2")
        self.assertEqual(remaining.count(), 1)
        self.assertEqual(remaining.first().resource_id, 200)
        
        # Verify audit entry created
        audit_entry = KernelAuditLog.objects.filter(
            event_type="RESOURCE_LOCK_RELEASED",
            decision_id="test-decision-2"
        ).first()
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.payload["resource_id"], "100")
    
    def test_release_allows_relock(self):
        """After physical delete, same resource tuple should be lockable again."""
        # Create lock
        lock1 = ResourceLock.create_lock(
            decision_id="test-decision-3",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=300,
            owner_id=1,
            expires_at=self.expires_at,
        )
        lock1_id = lock1.id
        
        # Release it
        count = ResourceLock.release_for_decision("test-decision-3")
        self.assertEqual(count, 1)
        
        # Verify deleted
        self.assertFalse(ResourceLock.objects.filter(id=lock1_id).exists())
        
        # Re-lock same resource tuple - should succeed without IntegrityError
        lock2 = ResourceLock.create_lock(
            decision_id="test-decision-3-v2",  # Different decision
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=300,  # Same resource_id
            owner_id=1,  # Same owner
            expires_at=self.expires_at,
        )
        
        self.assertIsNotNone(lock2)
        self.assertNotEqual(lock2.id, lock1_id)
        self.assertEqual(lock2.resource_id, 300)
    
    def test_full_release_idempotent(self):
        """Releasing missing decision should return 0 without error."""
        count = ResourceLock.release_for_decision("nonexistent-decision")
        self.assertEqual(count, 0)
    
    def test_partial_release_idempotent(self):
        """Releasing missing specific lock should return False without error."""
        success = ResourceLock.release_specific(
            decision_id="nonexistent",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=999,
        )
        self.assertFalse(success)
    
    def test_release_and_audit_instance_method(self):
        """Instance release_and_audit should delete and audit."""
        lock = ResourceLock.create_lock(
            decision_id="test-decision-4",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=400,
            owner_id=1,
            expires_at=self.expires_at,
        )
        lock_id = lock.id
        
        # Release via instance method
        success = lock.release_and_audit(reason="Instance release test")
        
        self.assertTrue(success)
        self.assertFalse(ResourceLock.objects.filter(id=lock_id).exists())
        
        # Verify audit entry
        audit_entry = KernelAuditLog.objects.filter(
            event_type="RESOURCE_LOCK_RELEASED",
            decision_id="test-decision-4"
        ).first()
        self.assertIsNotNone(audit_entry)
        self.assertIn("Instance release test", audit_entry.payload["reason"])
    
    def test_release_and_audit_idempotent_on_instance(self):
        """Calling release_and_audit twice should be safe."""
        lock = ResourceLock.create_lock(
            decision_id="test-decision-5",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=500,
            owner_id=1,
            expires_at=self.expires_at,
        )
        
        # First release
        success1 = lock.release_and_audit()
        self.assertTrue(success1)
        
        # Second release (lock already gone)
        success2 = lock.release_and_audit()
        self.assertFalse(success2)

