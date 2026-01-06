import uuid
import json
from django.test import TransactionTestCase, Client
from django.utils import timezone
from kernel.models import KernelAuditLog
from kernel.laws import KernelOutcome, AgentAction
from kernel.agent_sdk import (
    enforce_kernel_laws, 
    generate_context_hash, 
    KernelLawViolationError, 
    KernelABIError
)

class ComplianceAttributionTestCase(TransactionTestCase):
    """
    Verification suite for Day-4C: Compliance & Attribution.
    """
    
    def setUp(self):
        self.client = Client()
        KernelAuditLog.objects.all().delete()

    # --- TASK A & B: SDK ENFORCEMENT & HASHING ---

    def test_enforce_kernel_laws_valid(self):
        """Verify legal actions pass through."""
        # OK -> PROCEED is legal
        enforce_kernel_laws(KernelOutcome.OK, AgentAction.PROCEED)
        # REPLAY -> NOOP_SUCCESS is legal
        enforce_kernel_laws(KernelOutcome.REPLAY, AgentAction.NOOP_SUCCESS)

    def test_enforce_kernel_laws_violation(self):
        """Verify illegal actions raise KernelLawViolationError."""
        # CONFLICT -> PROCEED is ILLEGAL (must WAIT_RETRY)
        with self.assertRaises(KernelLawViolationError):
            enforce_kernel_laws(KernelOutcome.CONFLICT, AgentAction.PROCEED)

    def test_enforce_kernel_laws_forward_compatibility(self):
        """Verify unknown FAILED_ outcomes map to ABORT_ALERT."""
        # FAILED_SOMETHING_NEW -> ABORT_ALERT is legal
        enforce_kernel_laws("FAILED_SOMETHING_NEW", AgentAction.ABORT_ALERT)
        
        # FAILED_SOMETHING_NEW -> PROCEED is ILLEGAL
        with self.assertRaises(KernelLawViolationError):
            enforce_kernel_laws("FAILED_SOMETHING_NEW", AgentAction.PROCEED)

    def test_enforce_kernel_laws_abi_drift(self):
        """Verify completely unknown outcome raises KernelABIError."""
        with self.assertRaises(KernelABIError):
            enforce_kernel_laws("WHATS_THIS", AgentAction.PROCEED)

    def test_deterministic_context_hashing(self):
        """Verify hashing is stable across key ordering and whitespace."""
        ctx1 = {"agent_id": "A1", "task_id": "T1", "retry_epoch": 0}
        ctx2 = {"retry_epoch": 0, "task_id": "T1", "agent_id": "A1"} # Reordered
        
        h1 = generate_context_hash(ctx1)
        h2 = generate_context_hash(ctx2)
        
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64) # SHA-256

    # --- TASK C: OBSERVABILITY ATTRIBUTION ---

    def test_compliance_monitor_context_attribution(self):
        """Verify violation detection uses context_hash and provides attribution."""
        now = timezone.now()
        ctx_hash = generate_context_hash({"agent_id": "A1", "task_id": "T1"})
        owner_id = 99
        
        # Event 1: CONFLICT
        audit1 = KernelAuditLog.objects.create(
            event_type="SYS_CLAIM",
            payload={
                "request": {
                    "resource_type": "APPOINTMENT", 
                    "resource_id": 500, 
                    "owner_id": owner_id,
                    "context_hash": ctx_hash
                },
                "abi": {"outcome_code": "CONFLICT"}
            }
        )
        KernelAuditLog.objects.filter(id=audit1.id).update(created_at=now - timezone.timedelta(seconds=1))
        
        # Event 2: CONFLICT (Rapid Retry with same context)
        KernelAuditLog.objects.create(
            event_type="SYS_CLAIM",
            payload={
                "request": {
                    "resource_type": "APPOINTMENT", 
                    "resource_id": 500, 
                    "owner_id": owner_id,
                    "context_hash": ctx_hash
                },
                "abi": {"outcome_code": "CONFLICT"}
            }
        )
        
        response = self.client.get("/kernel/observability/compliance?window_ms=2000")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data["violations"]), 1)
        v = data["violations"][0]
        self.assertEqual(v["status"], "VIOLATION")
        self.assertEqual(v["owner_id"], owner_id)
        self.assertEqual(v["context_hash_tail"], ctx_hash[-8:])
        self.assertIn("Kernel Law Violation", v["reason"])
