import json
import uuid
import zlib
from datetime import timezone as py_timezone
from django.test import TransactionTestCase, Client
from django.utils import timezone
from kernel.models import KernelAuditLog
from decision_slots.models import ResourceLock

class KernelObservabilityTestCase(TransactionTestCase):
    """
    Test suite for read-only kernel observability APIs.
    """
    
    def setUp(self):
        self.client = Client()
        # Clean state
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()

    def test_audit_stream_field_formatting(self):
        """Verify audit endpoint returns all required fields and correct formatting."""
        # Setup: Create an audit entry
        event_id = uuid.uuid4()
        resource_id = 123
        payload = {
            "request": {
                "resource_type": "APPOINTMENT",
                "resource_id": resource_id
            },
            "abi": {
                "outcome_code": "OK"
            }
        }
        audit = KernelAuditLog.objects.create(
            event_id=event_id,
            event_type="SYS_CLAIM",
            decision_id="test:obs:001",
            payload=payload,
            status=KernelAuditLog.STATUS_HANDLED
        )
        
        response = self.client.get("/kernel/observability/audit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        item = data[0]
        
        self.assertEqual(item["id"], audit.id)
        self.assertEqual(item["syscall_name"], "SYS_CLAIM")
        self.assertEqual(item["resource_type"], "APPOINTMENT")
        self.assertEqual(item["resource_id"], resource_id)
        
        # MANDATORY: resource_id_hash derived from resource_id (not row id)
        expected_hash = f"#{resource_id % 1000:03d}"
        self.assertEqual(item["resource_id_hash"], expected_hash)
        
        self.assertEqual(item["outcome_code"], "OK")
        self.assertEqual(item["trace_id"], str(event_id))
        
        # MANDATORY: ISO-8601 with milliseconds, UTC suffix 'Z'
        created_at_str = item["created_at"]
        self.assertTrue(created_at_str.endswith("Z"))
        self.assertRegex(created_at_str, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")

    def test_audit_stream_non_int_resource_id_hash(self):
        """Verify resource_id_hash for non-integer resource IDs."""
        resource_id = "SERVER-BETA-4"
        audit = KernelAuditLog.objects.create(
            event_type="SYS_CLAIM",
            payload={"request": {"resource_id": resource_id}, "abi": {"outcome_code": "OK"}}
        )
        
        response = self.client.get("/kernel/observability/audit")
        data = response.json()
        item = data[0]
        
        # Calculate expected hash using zlib.crc32
        expected_val = zlib.crc32(resource_id.encode()) & 0xffffffff
        expected_hash = f"#{expected_val % 1000:03d}"
        self.assertEqual(item["resource_id_hash"], expected_hash)

    def test_audit_stream_ordering_and_filtering(self):
        """Verify ordering (DESC) and since_id/limit filtering."""
        for i in range(1, 6):
            KernelAuditLog.objects.create(
                event_type=f"EVENT_{i}",
                decision_id=f"dec_{i}",
                payload={"request": {"resource_id": i}, "abi": {"outcome_code": "OK"}}
            )
            
        # 1. Newest first (id DESC)
        response = self.client.get("/kernel/observability/audit?limit=2")
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["syscall_name"], "EVENT_5")
        self.assertEqual(data[1]["syscall_name"], "EVENT_4")
        
        # 2. since_id filter
        since_id = data[1]["id"]
        response = self.client.get(f"/kernel/observability/audit?since_id={since_id}")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["syscall_name"], "EVENT_5")

    def test_lock_snapshot_filtering(self):
        """Verify locks endpoint returns correct snapshot based on active_only flag."""
        now = timezone.now()
        
        # Active lock
        ResourceLock.objects.create(
            resource_type="APPOINTMENT",
            resource_id=1,
            owner_id=10,
            expires_at=now + timezone.timedelta(hours=1),
            status="active",
            decision_id="dec_active"
        )
        
        # Expired lock
        ResourceLock.objects.create(
            resource_type="APPOINTMENT",
            resource_id=2,
            owner_id=11,
            expires_at=now - timezone.timedelta(hours=1),
            status="active",
            decision_id="dec_expired"
        )
        
        # Released lock (inactive)
        ResourceLock.objects.create(
            resource_type="APPOINTMENT",
            resource_id=3,
            owner_id=12,
            expires_at=now + timezone.timedelta(hours=1),
            status="released",
            decision_id="dec_released"
        )

        # 1. active_only=true (default)
        response = self.client.get("/kernel/observability/locks")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["resource_id"], 1)
        
        # 2. active_only=false
        response = self.client.get("/kernel/observability/locks?active_only=false")
        data = response.json()
        self.assertEqual(len(data), 3)
        # Order: resource_type, resource_id
        ids = [item["resource_id"] for item in data]
        self.assertEqual(ids, [1, 2, 3])

    def test_pulse_view_accessibility(self):
        """Verify the kernel_pulse view is accessible (returns 200)."""
        response = self.client.get("/kernel/observability/pulse")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GateAI Kernel Pulse")
