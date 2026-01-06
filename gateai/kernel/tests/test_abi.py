"""
Tests for Kernel ABI (Application Binary Interface) v3.0

Validates stable contracts for execution outcomes and error codes.
"""

import uuid
from django.test import TestCase

from kernel.abi import (
    ABI_VERSION,
    KernelOutcome,
    KernelOutcomeCode,
    KernelErrorCode,
    classify_failure,
    classify_success,
    map_outcome_to_status,
    OUTCOME_TO_STATUS_MAP,
)
from kernel.models import KernelAuditLog


class OutcomeSchemaTestCase(TestCase):
    """Test ABI v3.0 outcome schema stability."""
    
    def test_outcome_schema_has_required_fields(self):
        """ABI v3.0 outcome must have all required fields."""
        outcome = KernelOutcome(
            abi_version="3.0",
            outcome_code=KernelOutcomeCode.OK,
            retryable=False,
            terminal=True,
            public_message="Test message",
        )
        data = outcome.to_dict()
        
        # Required fields
        self.assertIn("abi_version", data)
        self.assertIn("outcome_code", data)
        self.assertIn("retryable", data)
        self.assertIn("terminal", data)
        self.assertIn("public_message", data)
        
        # Values correct
        self.assertEqual(data["abi_version"], "3.0")
        self.assertEqual(data["outcome_code"], KernelOutcomeCode.OK)
        self.assertFalse(data["retryable"])
        self.assertTrue(data["terminal"])
    
    def test_outcome_serialization_roundtrip(self):
        """to_dict/from_dict must preserve data."""
        original = KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.FAILED_RETRYABLE,
            retryable=True,
            terminal=False,
            public_message="Test error",
            error_code=KernelErrorCode.KERNEL_LISTENER_EXCEPTION,
            internal_reason="Detail for debugging",
            http_hint=503,
            extras={"foo": "bar"},
        )
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = KernelOutcome.from_dict(data)
        
        # Verify all fields preserved
        self.assertEqual(restored.abi_version, original.abi_version)
        self.assertEqual(restored.outcome_code, original.outcome_code)
        self.assertEqual(restored.retryable, original.retryable)
        self.assertEqual(restored.terminal, original.terminal)
        self.assertEqual(restored.public_message, original.public_message)
        self.assertEqual(restored.error_code, original.error_code)
        self.assertEqual(restored.internal_reason, original.internal_reason)
        self.assertEqual(restored.http_hint, original.http_hint)
        self.assertEqual(restored.extras, original.extras)
    
    def test_outcome_abi_version_is_stable(self):
        """ABI version must always be 3.0 for this generation."""
        outcome = classify_success()
        self.assertEqual(outcome.abi_version, "3.0")
        self.assertEqual(ABI_VERSION, "3.0")
    
    def test_outcome_code_is_closed_set(self):
        """Outcome codes must be from KernelOutcomeCode (stable contract)."""
        valid_codes = {
            KernelOutcomeCode.OK,
            KernelOutcomeCode.REPLAY,
            KernelOutcomeCode.REJECTED,
            KernelOutcomeCode.CONFLICT,
            KernelOutcomeCode.FAILED_RETRYABLE,
            KernelOutcomeCode.FAILED_FATAL,
        }
        
        # Test all classification paths produce valid codes
        outcomes = [
            classify_success(claimed=True),
            classify_success(claimed=False),
            classify_failure(idempotency_replay=True),
            classify_failure(context_hash_mismatch=True),
            classify_failure(resource_conflict=True),
            classify_failure(callback_failure=True),
            classify_failure(exception=ValueError("test")),
        ]
        
        for outcome in outcomes:
            self.assertIn(outcome.outcome_code, valid_codes)


class ClassificationTestCase(TestCase):
    """Test deterministic failure/success classification."""
    
    def test_classify_idempotency_replay(self):
        """Idempotency replay -> REPLAY outcome."""
        outcome = classify_failure(idempotency_replay=True)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.REPLAY)
        self.assertTrue(outcome.terminal)
        self.assertFalse(outcome.retryable)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY)
        self.assertEqual(outcome.http_hint, 200)
    
    def test_classify_context_hash_mismatch(self):
        """Context hash mismatch -> REJECTED outcome."""
        outcome = classify_failure(context_hash_mismatch=True)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.REJECTED)
        self.assertTrue(outcome.terminal)
        self.assertFalse(outcome.retryable)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH)
        self.assertEqual(outcome.http_hint, 400)
    
    def test_classify_resource_conflict(self):
        """Resource conflict -> CONFLICT outcome."""
        outcome = classify_failure(resource_conflict=True)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.CONFLICT)
        self.assertFalse(outcome.terminal)
        self.assertTrue(outcome.retryable)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_RESOURCE_CONFLICT)
        self.assertEqual(outcome.http_hint, 409)
    
    def test_classify_listener_exception_retryable(self):
        """Generic exception -> FAILED_RETRYABLE."""
        test_exception = ValueError("Test error")
        outcome = classify_failure(exception=test_exception)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.FAILED_RETRYABLE)
        self.assertTrue(outcome.retryable)
        self.assertFalse(outcome.terminal)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_LISTENER_EXCEPTION)
        self.assertIn("Test error", outcome.internal_reason)
        self.assertEqual(outcome.http_hint, 503)
    
    def test_classify_callback_fatal(self):
        """Callback failure -> FAILED_FATAL."""
        outcome = classify_failure(callback_failure=True)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.FAILED_FATAL)
        self.assertFalse(outcome.retryable)
        self.assertTrue(outcome.terminal)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_CALLBACK_EXCEPTION)
        self.assertEqual(outcome.http_hint, 500)
    
    def test_classify_success_claimed(self):
        """Success with claimed=True -> OK."""
        outcome = classify_success(claimed=True)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.OK)
        self.assertTrue(outcome.terminal)
        self.assertFalse(outcome.retryable)
        self.assertIsNone(outcome.error_code)
        self.assertEqual(outcome.http_hint, 200)
    
    def test_classify_success_replay(self):
        """Success with claimed=False -> REPLAY."""
        outcome = classify_success(claimed=False)
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.REPLAY)
        self.assertTrue(outcome.terminal)
        self.assertFalse(outcome.retryable)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY)
        self.assertEqual(outcome.http_hint, 200)
    
    def test_classify_external_dependency_failure(self):
        """External dependency failure -> FAILED_RETRYABLE."""
        outcome = classify_failure(
            error_code=KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE
        )
        
        self.assertEqual(outcome.outcome_code, KernelOutcomeCode.FAILED_RETRYABLE)
        self.assertTrue(outcome.retryable)
        self.assertFalse(outcome.terminal)
        self.assertEqual(outcome.error_code, KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE)
        self.assertEqual(outcome.http_hint, 503)


class AuditStorageTestCase(TestCase):
    """Test ABI outcome storage in KernelAuditLog."""
    
    def test_kernel_audit_log_stores_outcome(self):
        """store_outcome() saves to payload["abi"]."""
        # Create audit log entry
        entry = KernelAuditLog.objects.create(
            event_type="TEST_EVENT",
            decision_id="test-1",
            idempotency_key="test-key-1",
            context_hash="abc123",
            status=KernelAuditLog.STATUS_EMITTED,
        )
        
        # Store outcome
        outcome = classify_success(claimed=True, message="Test success")
        success = KernelAuditLog.store_outcome(entry.event_id, outcome)
        
        self.assertTrue(success)
        
        # Verify stored
        entry.refresh_from_db()
        self.assertIn("abi", entry.payload)
        self.assertEqual(entry.payload["abi"]["outcome_code"], KernelOutcomeCode.OK)
        self.assertEqual(entry.payload["abi"]["abi_version"], "3.0")
    
    def test_kernel_audit_log_retrieves_outcome(self):
        """get_outcome() reconstructs from payload."""
        # Create audit log with outcome
        outcome = classify_failure(resource_conflict=True)
        entry = KernelAuditLog.objects.create(
            event_type="TEST_EVENT",
            decision_id="test-2",
            idempotency_key="test-key-2",
            context_hash="def456",
            status=KernelAuditLog.STATUS_FAILED,
            payload={"abi": outcome.to_dict()},
        )
        
        # Retrieve outcome
        retrieved = KernelAuditLog.get_outcome(entry.event_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.outcome_code, KernelOutcomeCode.CONFLICT)
        self.assertEqual(retrieved.error_code, KernelErrorCode.KERNEL_RESOURCE_CONFLICT)
        self.assertTrue(retrieved.retryable)
    
    def test_store_outcome_is_exception_safe(self):
        """store_outcome() never raises."""
        # Try to store to non-existent event
        fake_id = uuid.uuid4()
        outcome = classify_success()
        
        # Should return False, not raise
        success = KernelAuditLog.store_outcome(fake_id, outcome)
        self.assertFalse(success)
    
    def test_get_outcome_returns_none_for_missing(self):
        """get_outcome() returns None for non-existent event."""
        fake_id = uuid.uuid4()
        outcome = KernelAuditLog.get_outcome(fake_id)
        self.assertIsNone(outcome)


class StateMappingTestCase(TestCase):
    """Test outcome -> status mapping (Step 2 state machine preserved)."""
    
    def test_outcome_maps_to_status_deterministically(self):
        """Each outcome code maps to a valid KernelAuditLog status."""
        valid_statuses = {
            KernelAuditLog.STATUS_HANDLED,
            KernelAuditLog.STATUS_FAILED,
            KernelAuditLog.STATUS_REJECTED,
        }
        
        # Test all outcome codes map correctly
        mappings = {
            KernelOutcomeCode.OK: KernelAuditLog.STATUS_HANDLED,
            KernelOutcomeCode.REPLAY: KernelAuditLog.STATUS_REJECTED,
            KernelOutcomeCode.REJECTED: KernelAuditLog.STATUS_REJECTED,
            KernelOutcomeCode.CONFLICT: KernelAuditLog.STATUS_FAILED,
            KernelOutcomeCode.FAILED_RETRYABLE: KernelAuditLog.STATUS_FAILED,
            KernelOutcomeCode.FAILED_FATAL: KernelAuditLog.STATUS_FAILED,
        }
        
        for outcome_code, expected_status in mappings.items():
            outcome = KernelOutcome(
                abi_version=ABI_VERSION,
                outcome_code=outcome_code,
                retryable=False,
                terminal=True,
                public_message="Test",
            )
            status = map_outcome_to_status(outcome)
            self.assertEqual(status, expected_status)
            self.assertIn(status, valid_statuses)
    
    def test_outcome_http_hints_are_stable(self):
        """HTTP hints are consistent with outcome semantics."""
        # Success outcomes
        ok = classify_success(claimed=True)
        self.assertEqual(ok.http_hint, 200)
        
        replay = classify_success(claimed=False)
        self.assertEqual(replay.http_hint, 200)  # Successful replay is OK
        
        # Client error outcomes
        rejected = classify_failure(context_hash_mismatch=True)
        self.assertIn(rejected.http_hint, [400, 410])  # 4xx range
        
        # Conflict outcomes
        conflict = classify_failure(resource_conflict=True)
        self.assertEqual(conflict.http_hint, 409)
        
        # Server error outcomes
        retryable = classify_failure(exception=ValueError("test"))
        self.assertEqual(retryable.http_hint, 503)
        
        fatal = classify_failure(callback_failure=True)
        self.assertEqual(fatal.http_hint, 500)


class BackwardCompatibilityTestCase(TestCase):
    """Test Step 2 -> Step 3 backward compatibility."""
    
    def test_old_error_code_aliases_still_work(self):
        """Step 2 ErrorCode class still accessible via kernel_events."""
        from gateai.kernel_events import ErrorCode
        
        # Old names still work
        self.assertEqual(
            ErrorCode.LISTENER_EXCEPTION,
            KernelErrorCode.KERNEL_LISTENER_EXCEPTION
        )
        self.assertEqual(
            ErrorCode.CONTEXT_HASH_MISMATCH,
            KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH
        )
        self.assertEqual(
            ErrorCode.GENERIC_FAILURE,
            KernelErrorCode.KERNEL_GENERIC_FAILURE
        )
    
    def test_payment_error_code_maps_to_generic(self):
        """Old PAYMENT_EXECUTION_ERROR maps to domain-agnostic code."""
        from gateai.kernel_events import ErrorCode
        
        # Old payment-specific code now maps to generic external dependency
        self.assertEqual(
            ErrorCode.PAYMENT_EXECUTION_ERROR,
            KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE
        )
        
        # Verify it's not a domain-specific code
        self.assertIn("EXTERNAL_DEPENDENCY", ErrorCode.PAYMENT_EXECUTION_ERROR)
        self.assertNotIn("PAYMENT", KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE)


class ErrorCodeImmutabilityTestCase(TestCase):
    """Test error code stability (ABI contract)."""
    
    def test_all_error_codes_are_namespaced(self):
        """All error codes must use KERNEL/* namespace."""
        error_codes = [
            KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY,
            KernelErrorCode.KERNEL_IDEMPOTENCY_VIOLATION,
            KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH,
            KernelErrorCode.KERNEL_INVALID_PAYLOAD,
            KernelErrorCode.KERNEL_LISTENER_EXCEPTION,
            KernelErrorCode.KERNEL_CALLBACK_EXCEPTION,
            KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE,
            KernelErrorCode.KERNEL_RESOURCE_LOCK_EXPIRED,
            KernelErrorCode.KERNEL_RESOURCE_CONFLICT,
            KernelErrorCode.KERNEL_GENERIC_FAILURE,
        ]
        
        for code in error_codes:
            self.assertTrue(
                code.startswith("KERNEL/"),
                f"Error code {code} must use KERNEL/* namespace"
            )
    
    def test_error_codes_are_domain_agnostic(self):
        """Error codes must not reference domain concepts."""
        forbidden_terms = ["PAYMENT", "APPOINTMENT", "MENTOR", "USER", "JOB"]
        
        error_codes = [
            KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY,
            KernelErrorCode.KERNEL_IDEMPOTENCY_VIOLATION,
            KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH,
            KernelErrorCode.KERNEL_INVALID_PAYLOAD,
            KernelErrorCode.KERNEL_LISTENER_EXCEPTION,
            KernelErrorCode.KERNEL_CALLBACK_EXCEPTION,
            KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE,
            KernelErrorCode.KERNEL_RESOURCE_LOCK_EXPIRED,
            KernelErrorCode.KERNEL_RESOURCE_CONFLICT,
            KernelErrorCode.KERNEL_GENERIC_FAILURE,
        ]
        
        for code in error_codes:
            for term in forbidden_terms:
                self.assertNotIn(
                    term,
                    code,
                    f"Error code {code} must not reference domain concept {term}"
                )

