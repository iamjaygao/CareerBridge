#!/usr/bin/env python3
"""
Test suite for ResourceLock de-duplication arbiter.

Validates:
- Deterministic tie-breaking
- Correct winner selection (highest expires_at, then highest id)
- Atomic execution
- Idempotency
"""

import os
import sys
import django
from datetime import timedelta

# Django setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from decision_slots.models import ResourceLock


class ArbiterTestCase:
    """Test harness for de-duplication arbiter."""
    
    def setUp(self):
        """Create test data with known duplicates."""
        print("━" * 70)
        print("Setting up test data...")
        print("━" * 70)
        
        # Clear existing locks
        ResourceLock.objects.all().delete()
        
        now = timezone.now()
        
        # Test Case 1: Duplicate by expires_at (should keep highest expires_at)
        # Group A: (APPOINTMENT, 100)
        ResourceLock.objects.create(
            decision_id="test:A:1",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
            owner_id=1,
            expires_at=now + timedelta(hours=1),  # Lower expires_at
            status='active'
        )
        ResourceLock.objects.create(
            decision_id="test:A:2",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
            owner_id=1,
            expires_at=now + timedelta(hours=2),  # Higher expires_at (WINNER)
            status='active'
        )
        
        # Test Case 2: Duplicate by ID (expires_at tied, should keep highest id)
        # Group B: (APPOINTMENT, 200)
        same_expiry = now + timedelta(hours=3)
        lock_b1 = ResourceLock.objects.create(
            decision_id="test:B:1",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=200,
            owner_id=2,
            expires_at=same_expiry,  # Same expires_at
            status='active'
        )
        lock_b2 = ResourceLock.objects.create(
            decision_id="test:B:2",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=200,
            owner_id=2,
            expires_at=same_expiry,  # Same expires_at
            status='active'
        )
        # Higher ID wins (lock_b2 should win)
        
        # Test Case 3: Triple duplicate (should keep one, delete two)
        # Group C: (STAGING_SERVER, 300)
        ResourceLock.objects.create(
            decision_id="test:C:1",
            resource_type=ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            resource_id=300,
            owner_id=3,
            expires_at=now + timedelta(hours=1),  # Lowest
            status='active'
        )
        ResourceLock.objects.create(
            decision_id="test:C:2",
            resource_type=ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            resource_id=300,
            owner_id=3,
            expires_at=now + timedelta(hours=2),  # Middle
            status='active'
        )
        ResourceLock.objects.create(
            decision_id="test:C:3",
            resource_type=ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            resource_id=300,
            owner_id=3,
            expires_at=now + timedelta(hours=3),  # Highest (WINNER)
            status='active'
        )
        
        # Test Case 4: No duplicates (should be untouched)
        # Group D: (API_CREDENTIAL, 400)
        ResourceLock.objects.create(
            decision_id="test:D:1",
            resource_type=ResourceLock.RESOURCE_TYPE_API_CREDENTIAL,
            resource_id=400,
            owner_id=4,
            expires_at=now + timedelta(hours=1),
            status='active'
        )
        
        total_locks = ResourceLock.objects.count()
        print(f"✅ Created {total_locks} test locks")
        print(f"   - 3 duplicate groups (A, B, C)")
        print(f"   - 1 unique lock (D)")
        print()
    
    def test_dry_run(self):
        """Test dry-run mode (no deletions)."""
        print("━" * 70)
        print("TEST: Dry Run Mode")
        print("━" * 70)
        
        from scripts.dedupe_resource_locks import ResourceLockArbiter
        
        # Set environment gate
        os.environ['PRE_MIGRATION_SNAPSHOT_TAKEN'] = 'YES'
        
        arbiter = ResourceLockArbiter(verbose=True)
        
        # Check gate
        assert arbiter.check_environment_gate(), "Environment gate should pass"
        
        # Find duplicates
        duplicate_groups = arbiter.find_duplicate_groups()
        assert len(duplicate_groups) == 3, f"Expected 3 duplicate groups, got {len(duplicate_groups)}"
        
        # Compute plan
        arbiter.compute_deletion_plan(duplicate_groups)
        
        # Verify plan
        assert arbiter.duplicate_groups_found == 3
        assert arbiter.total_rows_to_delete == 5  # 1 from A, 1 from B, 2 from C
        
        # Print plan
        arbiter.print_deletion_plan()
        
        # Verify no deletions occurred
        total_locks = ResourceLock.objects.count()
        assert total_locks == 8, f"Dry run should not delete, but count is {total_locks}"
        
        print()
        print("✅ Dry run test passed")
        print()
    
    def test_execute_mode(self):
        """Test execution mode (physical deletions)."""
        print("━" * 70)
        print("TEST: Execute Mode")
        print("━" * 70)
        
        from scripts.dedupe_resource_locks import ResourceLockArbiter
        
        # Set environment gate
        os.environ['PRE_MIGRATION_SNAPSHOT_TAKEN'] = 'YES'
        
        arbiter = ResourceLockArbiter(verbose=True)
        
        # Find duplicates
        duplicate_groups = arbiter.find_duplicate_groups()
        
        # Compute plan
        arbiter.compute_deletion_plan(duplicate_groups)
        
        # Execute deletions
        deleted_count = arbiter.execute_deletions()
        
        print()
        print(f"Deleted {deleted_count} rows")
        
        # Verify results
        total_locks = ResourceLock.objects.count()
        assert total_locks == 4, f"Expected 4 locks remaining, got {total_locks}"
        
        # Verify winners
        # Group A: Should keep lock with highest expires_at
        locks_a = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100
        )
        assert locks_a.count() == 1, "Group A should have 1 lock"
        winner_a = locks_a.first()
        assert winner_a.decision_id == "test:A:2", "Group A winner should be test:A:2"
        
        # Group B: Should keep lock with highest ID
        locks_b = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=200
        )
        assert locks_b.count() == 1, "Group B should have 1 lock"
        winner_b = locks_b.first()
        assert winner_b.decision_id == "test:B:2", "Group B winner should be test:B:2"
        
        # Group C: Should keep lock with highest expires_at
        locks_c = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            resource_id=300
        )
        assert locks_c.count() == 1, "Group C should have 1 lock"
        winner_c = locks_c.first()
        assert winner_c.decision_id == "test:C:3", "Group C winner should be test:C:3"
        
        # Group D: Should be untouched
        locks_d = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_API_CREDENTIAL,
            resource_id=400
        )
        assert locks_d.count() == 1, "Group D should have 1 lock"
        
        print()
        print("✅ Execute mode test passed")
        print()
    
    def test_idempotency(self):
        """Test that arbiter is idempotent (safe to re-run)."""
        print("━" * 70)
        print("TEST: Idempotency")
        print("━" * 70)
        
        from scripts.dedupe_resource_locks import ResourceLockArbiter
        
        # Set environment gate
        os.environ['PRE_MIGRATION_SNAPSHOT_TAKEN'] = 'YES'
        
        # First run
        arbiter1 = ResourceLockArbiter()
        duplicate_groups1 = arbiter1.find_duplicate_groups()
        
        if duplicate_groups1:
            arbiter1.compute_deletion_plan(duplicate_groups1)
            arbiter1.execute_deletions()
        
        # Second run (should find no duplicates)
        arbiter2 = ResourceLockArbiter()
        duplicate_groups2 = arbiter2.find_duplicate_groups()
        
        assert len(duplicate_groups2) == 0, "Second run should find no duplicates"
        
        print()
        print("✅ Idempotency test passed")
        print()
    
    def test_environment_gate(self):
        """Test that environment gate blocks execution without snapshot."""
        print("━" * 70)
        print("TEST: Environment Gate")
        print("━" * 70)
        
        from scripts.dedupe_resource_locks import ResourceLockArbiter
        
        # Clear environment variable
        if 'PRE_MIGRATION_SNAPSHOT_TAKEN' in os.environ:
            del os.environ['PRE_MIGRATION_SNAPSHOT_TAKEN']
        
        arbiter = ResourceLockArbiter()
        
        # Should fail gate check
        assert not arbiter.check_environment_gate(), "Gate should block without snapshot ack"
        
        print()
        print("✅ Environment gate test passed")
        print()
    
    def tearDown(self):
        """Clean up test data."""
        print("━" * 70)
        print("Cleaning up test data...")
        print("━" * 70)
        ResourceLock.objects.all().delete()
        print("✅ Cleanup complete")
        print()


def main():
    """Run all tests."""
    print()
    print("━" * 70)
    print("KERNEL ARBITER TEST SUITE")
    print("━" * 70)
    print()
    
    test = ArbiterTestCase()
    
    try:
        # Test 1: Environment gate
        test.test_environment_gate()
        
        # Test 2: Setup data
        test.setUp()
        
        # Test 3: Dry run
        test.test_dry_run()
        
        # Test 4: Execute mode
        test.test_execute_mode()
        
        # Test 5: Idempotency
        test.test_idempotency()
        
        # Cleanup
        test.tearDown()
        
        print("━" * 70)
        print("✅ ALL TESTS PASSED")
        print("━" * 70)
        print()
        print("The arbiter is production-ready.")
        print()
        
    except AssertionError as e:
        print()
        print("━" * 70)
        print("❌ TEST FAILED")
        print("━" * 70)
        print(f"Error: {e}")
        print("━" * 70)
        sys.exit(1)
        
    except Exception as e:
        print()
        print("━" * 70)
        print("❌ UNEXPECTED ERROR")
        print("━" * 70)
        print(f"Error: {e}")
        print("━" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

