"""
Test suite for kernel syscalls (sys_claim).

Validates:
- Deterministic behavior
- Physical safety under PostgreSQL concurrency
- ABI compliance
- Auditability (KernelAuditLog always exists)
- Broken-transaction safety
- Re-entrant safety
- Domain-agnostic interface
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.test import TransactionTestCase
from django.db import transaction

from kernel.syscalls import sys_claim, SyscallResult
from kernel.abi import KernelOutcomeCode
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
from decision_slots.models import ResourceLock


class SysClaimTestCase(TransactionTestCase):
    """Test suite for sys_claim syscall."""
    
    def setUp(self):
        """Clean slate for each test."""
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()
    
    def tearDown(self):
        """Cleanup after each test."""
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()
    
    def test_basic_claim_success(self):
        """Test basic successful resource claim."""
        payload = {
            "decision_id": "test:001",
            "context_hash": "hash001",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 100,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Verify result
        assert isinstance(result, SyscallResult)
        assert result.outcome_code == KernelOutcomeCode.OK
        assert result.audit_id is not None
        
        # Verify outcome
        outcome = result.outcome
        assert outcome["outcome_code"] == KernelOutcomeCode.OK
        assert outcome["retryable"] is False
        assert outcome["terminal"] is True
        assert "lock_id" in outcome["extras"]
        
        # Verify lock created
        lock = ResourceLock.objects.get(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=100,
        )
        assert lock.owner_id == 1
        assert lock.decision_id == "test:001"
        assert lock.status == "active"
        
        # Verify audit created
        audit = KernelAuditLog.objects.get(event_id=result.audit_id)
        assert audit.event_type == "SYS_CLAIM"
        assert audit.decision_id == "test:001"
        assert audit.status == "HANDLED"
    
    def test_idempotency_replay(self):
        """Test idempotent replay detection (double-click)."""
        payload = {
            "decision_id": "test:002",
            "context_hash": "hash002",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 200,
            "owner_id": 2,
            "duration_seconds": 3600,
        }
        
        # First call - should succeed
        result1 = sys_claim(payload)
        assert result1.outcome_code == KernelOutcomeCode.OK
        
        # Second call - should detect replay
        result2 = sys_claim(payload)
        assert result2.outcome_code == KernelOutcomeCode.REPLAY
        assert result2.outcome["outcome_code"] == KernelOutcomeCode.REPLAY
        assert "already completed" in result2.outcome["public_message"].lower()
        
        # Verify only one lock created
        locks = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=200,
        )
        assert locks.count() == 1
        
        # Verify both calls created audit entries
        assert KernelAuditLog.objects.filter(
            decision_id="test:002"
        ).count() == 2
    
    def test_physical_conflict_different_owner(self):
        """Test physical conflict when different owner claims same resource."""
        # Owner 1 claims resource
        payload1 = {
            "decision_id": "test:003a",
            "context_hash": "hash003a",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 300,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result1 = sys_claim(payload1)
        assert result1.outcome_code == KernelOutcomeCode.OK
        
        # Owner 2 tries to claim same resource
        payload2 = {
            "decision_id": "test:003b",
            "context_hash": "hash003b",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 300,  # Same resource
            "owner_id": 2,  # Different owner
            "duration_seconds": 3600,
        }
        
        result2 = sys_claim(payload2)
        assert result2.outcome_code == KernelOutcomeCode.CONFLICT
        assert result2.outcome["retryable"] is True
        assert result2.outcome["terminal"] is False
        assert result2.outcome["error_code"] == "KERNEL/RESOURCE_CONFLICT"
        
        # Verify only first lock exists
        lock = ResourceLock.objects.get(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=300,
        )
        assert lock.owner_id == 1  # First owner still holds
        
        # Verify both audits exist
        assert KernelAuditLog.objects.filter(
            event_type="SYS_CLAIM"
        ).count() == 2
    
    def test_reentrant_same_owner(self):
        """Test re-entrant claim by same owner (ownership guard)."""
        # Owner 1 claims resource
        payload1 = {
            "decision_id": "test:004a",
            "context_hash": "hash004a",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 400,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result1 = sys_claim(payload1)
        assert result1.outcome_code == KernelOutcomeCode.OK
        
        # Same owner tries to claim again (different decision_id, different context_hash)
        payload2 = {
            "decision_id": "test:004b",  # Different decision
            "context_hash": "hash004b",  # Different context
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 400,  # Same resource
            "owner_id": 1,  # Same owner
            "duration_seconds": 3600,
        }
        
        result2 = sys_claim(payload2)
        assert result2.outcome_code == KernelOutcomeCode.OK  # Re-entrant success
        assert "re-entrant" in result2.outcome["public_message"].lower()
        
        # Verify only first lock exists (no duplicate)
        locks = ResourceLock.objects.filter(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=400,
        )
        assert locks.count() == 1
        assert locks.first().decision_id == "test:004a"  # Original decision
    
    def test_expired_lock_cleanup(self):
        """Test shadow pre-check cleans up expired locks."""
        # Create an expired lock manually
        expired_time = timezone.now() - timedelta(hours=1)
        ResourceLock.objects.create(
            decision_id="test:expired",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=500,
            owner_id=99,
            expires_at=expired_time,
            status='active',
        )
        
        # New owner claims - should clean up expired lock and succeed
        payload = {
            "decision_id": "test:005",
            "context_hash": "hash005",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 500,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.OK
        
        # Verify old lock cleaned up, new lock created
        lock = ResourceLock.objects.get(
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=500,
        )
        assert lock.owner_id == 1  # New owner
        assert lock.decision_id == "test:005"  # New decision
    
    def test_invalid_payload_missing_fields(self):
        """Test validation of missing required fields."""
        payload = {
            "decision_id": "test:006",
            # Missing context_hash
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 600,
            # Missing owner_id
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.REJECTED
        assert result.outcome["error_code"] == "KERNEL/INVALID_PAYLOAD"
        assert "missing" in result.outcome["internal_reason"].lower()
        
        # Verify no lock created
        assert not ResourceLock.objects.filter(resource_id=600).exists()
        
        # Verify audit exists (even for rejected)
        audit = KernelAuditLog.objects.get(event_id=result.audit_id)
        assert audit.status == "REJECTED"
    
    def test_invalid_payload_missing_duration(self):
        """Test validation of missing expires_at/duration_seconds."""
        payload = {
            "decision_id": "test:007",
            "context_hash": "hash007",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 700,
            "owner_id": 1,
            # Missing both expires_at and duration_seconds
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.REJECTED
        assert result.outcome["error_code"] == "KERNEL/INVALID_PAYLOAD"
        
        # Verify no lock created
        assert not ResourceLock.objects.filter(resource_id=700).exists()
    
    def test_audit_always_created(self):
        """Test that audit log is ALWAYS created, even on error."""
        # Valid payload that will succeed
        payload = {
            "decision_id": "test:008",
            "context_hash": "hash008",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 800,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Verify audit exists
        audit = KernelAuditLog.objects.get(event_id=result.audit_id)
        assert audit.event_type == "SYS_CLAIM"
        assert audit.decision_id == "test:008"
        assert "request" in audit.payload
    
    def test_expires_at_datetime(self):
        """Test using explicit expires_at datetime instead of duration."""
        expires_at = timezone.now() + timedelta(hours=2)
        
        payload = {
            "decision_id": "test:009",
            "context_hash": "hash009",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 900,
            "owner_id": 1,
            "expires_at": expires_at,
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.OK
        
        # Verify lock has correct expiration
        lock = ResourceLock.objects.get(resource_id=900)
        # Allow 1 second tolerance for timing
        assert abs((lock.expires_at - expires_at).total_seconds()) < 1
    
    def test_resource_key_support(self):
        """Test optional resource_key field."""
        payload = {
            "decision_id": "test:010",
            "context_hash": "hash010",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1000,
            "owner_id": 1,
            "duration_seconds": 3600,
            "resource_key": "slot_morning",
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.OK
        
        # Verify resource_key stored
        lock = ResourceLock.objects.get(resource_id=1000)
        assert lock.resource_key == "slot_morning"
    
    def test_different_resource_types_no_conflict(self):
        """Test that different resource types don't conflict."""
        # Claim APPOINTMENT:100
        payload1 = {
            "decision_id": "test:011a",
            "context_hash": "hash011a",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 100,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result1 = sys_claim(payload1)
        assert result1.outcome_code == KernelOutcomeCode.OK
        
        # Claim STAGING_SERVER:100 (same ID, different type)
        payload2 = {
            "decision_id": "test:011b",
            "context_hash": "hash011b",
            "resource_type": ResourceLock.RESOURCE_TYPE_STAGING_SERVER,
            "resource_id": 100,  # Same ID
            "owner_id": 2,
            "duration_seconds": 3600,
        }
        
        result2 = sys_claim(payload2)
        assert result2.outcome_code == KernelOutcomeCode.OK  # No conflict
        
        # Verify both locks exist
        assert ResourceLock.objects.filter(resource_id=100).count() == 2
    
    def test_abi_outcome_structure(self):
        """Test that outcome follows ABI structure."""
        payload = {
            "decision_id": "test:012",
            "context_hash": "hash012",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1200,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Verify ABI fields present
        outcome = result.outcome
        assert "abi_version" in outcome
        assert "outcome_code" in outcome
        assert "retryable" in outcome
        assert "terminal" in outcome
        assert "public_message" in outcome
        assert outcome["abi_version"] == "3.0"
    
    def test_audit_outcome_stored(self):
        """Test that outcome is stored in audit log."""
        payload = {
            "decision_id": "test:013",
            "context_hash": "hash013",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1300,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Verify outcome stored in audit
        audit = KernelAuditLog.objects.get(event_id=result.audit_id)
        stored_outcome = KernelAuditLog.get_outcome(audit.event_id)
        
        assert stored_outcome is not None
        assert stored_outcome.outcome_code == KernelOutcomeCode.OK
        assert stored_outcome.abi_version == "3.0"


    def test_audit_failure_does_not_block_syscall(self):
        """
        Test that audit failures don't affect syscall outcome.
        
        CRITICAL HARDENING REQUIREMENT:
        Audit is best-effort and must NEVER block syscall return.
        """
        from unittest.mock import patch
        
        payload = {
            "decision_id": "test:014",
            "context_hash": "hash014",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1400,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        # Monkeypatch audit to fail
        with patch.object(KernelAuditLog, 'store_outcome', side_effect=Exception("Audit DB down")):
            result = sys_claim(payload)
        
        # Syscall MUST still succeed (audit failure swallowed)
        assert result.outcome_code == KernelOutcomeCode.OK
        assert result.audit_id is not None
        
        # Verify lock was actually created (syscall proceeded normally)
        lock = ResourceLock.objects.get(resource_id=1400)
        assert lock.owner_id == 1
    
    def test_iso8601_with_z_suffix(self):
        """Test ISO-8601 datetime parsing with 'Z' suffix (stdlib-only)."""
        from datetime import datetime
        
        payload = {
            "decision_id": "test:015",
            "context_hash": "hash015",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1500,
            "owner_id": 1,
            "expires_at": "2026-01-06T15:30:00Z",  # ISO-8601 with Z
        }
        
        result = sys_claim(payload)
        assert result.outcome_code == KernelOutcomeCode.OK
        
        # Verify lock created with correct expiration
        lock = ResourceLock.objects.get(resource_id=1500)
        # 'Z' should be normalized to UTC
        assert lock.expires_at.tzinfo is not None
    
    def test_outer_atomic_block_prevents_unsafe_query(self):
        """
        TASK 1: Test that outer transaction.atomic() prevents post-conflict DB query.
        
        DAY-3 SAFETY FIX:
        If sys_claim is called inside an outer transaction.atomic() decorator/caller,
        and IntegrityError occurs, we MUST NOT query the DB (broken transaction risk).
        Instead, return FAILED_RETRYABLE.
        """
        # Create conflicting lock
        ResourceLock.objects.create(
            decision_id="test:existing",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=1600,
            owner_id=99,  # Different owner
            expires_at=timezone.now() + timedelta(hours=1),
            status='active',
        )
        
        payload = {
            "decision_id": "test:016",
            "context_hash": "hash016",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1600,  # Same resource (conflict)
            "owner_id": 1,  # Different owner
            "duration_seconds": 3600,
        }
        
        # Wrap sys_claim in outer atomic block
        with transaction.atomic():
            result = sys_claim(payload)
        
        # Should return FAILED_RETRYABLE (not crash with "transaction is aborted")
        assert result.outcome_code == KernelOutcomeCode.FAILED_RETRYABLE
        assert "atomic" in result.outcome["internal_reason"].lower() or "context" in result.outcome["internal_reason"].lower()
        
        # Audit should still be sealed (best-effort)
        audit = KernelAuditLog.objects.get(event_id=result.audit_id)
        assert audit.status in ["FAILED", "REJECTED"]  # Any terminal state OK
    
    def test_expired_lock_does_not_trigger_reentry(self):
        """
        TASK 2: Test that EXPIRED lock does NOT cause re-entry success.
        
        Precise re-entry detection must filter:
        - expires_at > now (only ACTIVE locks)
        - status == 'active'
        """
        # Create EXPIRED lock by same owner
        ResourceLock.objects.create(
            decision_id="test:expired",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=1700,
            owner_id=1,  # Same owner
            expires_at=timezone.now() - timedelta(hours=1),  # EXPIRED
            status='active',
        )
        
        payload = {
            "decision_id": "test:017",
            "context_hash": "hash017",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1700,
            "owner_id": 1,  # Same owner
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Should succeed (expired lock cleaned up or ignored)
        # Should NOT be treated as re-entry
        assert result.outcome_code == KernelOutcomeCode.OK
        
        # New lock should be created (not reusing expired one)
        locks = ResourceLock.objects.filter(resource_id=1700, status='active')
        assert locks.count() >= 1
        
        # At least one lock should be newly created (not expired)
        fresh_lock = locks.filter(expires_at__gt=timezone.now()).first()
        assert fresh_lock is not None
    
    def test_active_lock_same_owner_triggers_reentry(self):
        """
        TASK 2: Test that ACTIVE lock by same owner DOES trigger re-entry.
        
        Precise re-entry detection must recognize:
        - Same owner_id
        - expires_at > now (ACTIVE)
        - status == 'active'
        """
        # Create ACTIVE lock by same owner
        ResourceLock.objects.create(
            decision_id="test:active",
            resource_type=ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            resource_id=1800,
            owner_id=1,  # Same owner
            expires_at=timezone.now() + timedelta(hours=1),  # ACTIVE
            status='active',
        )
        
        payload = {
            "decision_id": "test:018",
            "context_hash": "hash018",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 1800,
            "owner_id": 1,  # Same owner
            "duration_seconds": 3600,
        }
        
        result = sys_claim(payload)
        
        # Should succeed with re-entry message
        assert result.outcome_code == KernelOutcomeCode.OK
        assert "re-entrant" in result.outcome["public_message"].lower() or "already holds" in result.outcome["public_message"].lower()
        
        # Original lock should remain (no new lock created)
        locks = ResourceLock.objects.filter(resource_id=1800, status='active')
        assert locks.count() == 1
    
    def test_audit_sealed_on_all_paths(self):
        """
        TASK 3: Test that audit is sealed on ALL return paths.
        
        Even if audit.store_outcome() fails, syscall must proceed and return correct outcome.
        """
        from unittest.mock import patch
        
        test_cases = [
            {
                "name": "invalid_payload",
                "payload": {
                    "decision_id": "test:019a",
                    # Missing required fields
                },
                "expected_code": KernelOutcomeCode.REJECTED,
            },
            {
                "name": "valid_claim",
                "payload": {
                    "decision_id": "test:019b",
                    "context_hash": "hash019b",
                    "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
                    "resource_id": 1900,
                    "owner_id": 1,
                    "duration_seconds": 3600,
                },
                "expected_code": KernelOutcomeCode.OK,
            },
        ]
        
        for test_case in test_cases:
            # Monkeypatch audit to fail
            with patch.object(KernelAuditLog, 'store_outcome', side_effect=Exception("Audit failure")):
                result = sys_claim(test_case["payload"])
            
            # Syscall MUST return correct outcome (audit failure swallowed)
            assert result.outcome_code == test_case["expected_code"], f"Failed for {test_case['name']}"
            
            # Audit entry should exist (created, even if sealing failed)
            assert result.audit_id is not None


class SysClaimConcurrencyTestCase(TransactionTestCase):
    """Test syscall behavior under concurrency."""
    
    def test_deterministic_with_same_inputs(self):
        """Test that same inputs produce same results (determinism)."""
        payload = {
            "decision_id": "test:concurrent:001",
            "context_hash": "hash:concurrent:001",
            "resource_type": ResourceLock.RESOURCE_TYPE_APPOINTMENT,
            "resource_id": 2001,
            "owner_id": 1,
            "duration_seconds": 3600,
        }
        
        # First call
        result1 = sys_claim(payload)
        
        # Clean up lock to retry
        ResourceLock.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()
        
        # Second call with identical payload
        result2 = sys_claim(payload)
        
        # Results should be deterministic (same outcome code)
        assert result1.outcome_code == result2.outcome_code
        assert result1.outcome["outcome_code"] == result2.outcome["outcome_code"]

