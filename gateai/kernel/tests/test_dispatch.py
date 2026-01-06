import json
import uuid
from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.utils import timezone
from kernel.abi import KernelOutcomeCode
from decision_slots.models import ResourceLock

class KernelDispatchTestCase(TransactionTestCase):
    """
    Test suite for the syscall HTTP entrypoint: POST /kernel/dispatch
    """
    
    def setUp(self):
        self.client = Client()
        self.url = "/kernel/dispatch"
        # Ensure clean state
        ResourceLock.objects.all().delete()

    def test_valid_sys_claim_dispatch(self):
        """1) Valid sys_claim dispatch → HTTP 200 + outcome_code OK"""
        payload = {
            "decision_id": "test:dispatch:001",
            "context_hash": "hash001",
            "resource_type": "APPOINTMENT",
            "resource_id": 101,
            "owner_id": 1,
            "duration_seconds": 3600
        }
        body = {
            "syscall_name": "sys_claim",
            "payload": payload
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["outcome_code"], KernelOutcomeCode.OK)
        self.assertIn("trace_id", data)
        self.assertEqual(response["X-GateAI-TraceID"], data["trace_id"])
        
        # Verify lock actually created
        self.assertTrue(ResourceLock.objects.filter(resource_id=101).exists())

    def test_conflict_scenario(self):
        """2) Conflict scenario → HTTP 409 + outcome_code CONFLICT"""
        # Manually create a conflicting lock
        ResourceLock.objects.create(
            decision_id="existing:lock",
            resource_type="APPOINTMENT",
            resource_id=202,
            owner_id=99,
            expires_at=timezone.now() + timezone.timedelta(hours=1),
            status="active"
        )
        
        payload = {
            "decision_id": "test:dispatch:002",
            "context_hash": "hash002",
            "resource_type": "APPOINTMENT",
            "resource_id": 202,  # Same resource
            "owner_id": 1,      # Different owner
            "duration_seconds": 3600
        }
        body = {
            "syscall_name": "sys_claim",
            "payload": payload
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data["outcome_code"], KernelOutcomeCode.CONFLICT)
        self.assertIn("X-GateAI-TraceID", response)

    def test_unsupported_syscall_name(self):
        """3) Unsupported syscall_name → HTTP 400 and message contains 'unsupported syscall'"""
        body = {
            "syscall_name": "sys_reboot",  # Unsupported
            "payload": {"some": "data"}
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("trace_id", data)
        self.assertIn("message", data)
        self.assertIn("unsupported syscall", data["message"].lower())

    def test_malformed_body(self):
        """Non-object body or missing fields → HTTP 400"""
        # Case A: Not an object
        response = self.client.post(
            self.url,
            data="not a json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        
        # Case B: Missing syscall_name
        body = {"payload": {}}
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("message", response.json())

    def test_trace_id_propagation(self):
        """Trace ID propagation: send X-Trace-Id header; ensure response X-GateAI-TraceID equals it"""
        custom_trace_id = str(uuid.uuid4())
        payload = {
            "decision_id": "test:dispatch:003",
            "context_hash": "hash003",
            "resource_type": "APPOINTMENT",
            "resource_id": 303,
            "owner_id": 1,
            "duration_seconds": 3600
        }
        body = {
            "syscall_name": "sys_claim",
            "payload": payload
        }
        
        # Using HTTP_X_TRACE_ID because Django converts headers to HTTP_*
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json",
            HTTP_X_TRACE_ID=custom_trace_id
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-GateAI-TraceID"], custom_trace_id)
        self.assertEqual(response.json()["trace_id"], custom_trace_id)

    def test_invalid_payload_rejected(self):
        """Invalid payload → HTTP 400 + outcome_code REJECTED (canonical name)"""
        payload = {
            "decision_id": "test:dispatch:004",
            # Missing context_hash
            "resource_type": "APPOINTMENT",
            "resource_id": 404,
            "owner_id": 1,
            "duration_seconds": 3600
        }
        body = {
            "syscall_name": "sys_claim",
            "payload": payload
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["outcome_code"], KernelOutcomeCode.REJECTED)
