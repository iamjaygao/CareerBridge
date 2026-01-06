from django.test import TestCase
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import timedelta

from decision_slots.models import ResourceLock


class TestPhysicalUniqueBarrier(TestCase):
    def test_physical_concurrency_barrier(self):
        ResourceLock.objects.filter(resource_type="V1", resource_id=1).delete()

        ResourceLock.objects.create(
            decision_id="t1",
            resource_type="V1",
            resource_id=1,
            owner_id=1,
            expires_at=timezone.now() + timedelta(seconds=30),
        )

        with self.assertRaises(IntegrityError):
            ResourceLock.objects.create(
                decision_id="t2",
                resource_type="V1",
                resource_id=1,
                owner_id=2,
                expires_at=timezone.now() + timedelta(seconds=30),
            )
