"""
Real concurrency tests for sys_claim (PostgreSQL, READ COMMITTED).

Each scenario runs ITERATIONS times (default 100) with N threads on separate
connections, released by a barrier, and asserts exactly one winner.
"""

from collections import Counter
from datetime import timedelta

from django.test import TransactionTestCase
from django.utils import timezone

from decision_slots.models import ResourceLock
from kernel.abi import KernelOutcomeCode as Code
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
from kernel.syscalls import sys_claim

from .concurrency import ITERATIONS, requires_postgres, run_concurrently

APPT = ResourceLock.RESOURCE_TYPE_APPOINTMENT
N = 8


def claim(owner, resource_id, decision, ctx='k'):
    return sys_claim({
        'decision_id': decision, 'context_hash': ctx, 'resource_type': APPT,
        'resource_id': resource_id, 'owner_id': owner, 'duration_seconds': 600,
    }).outcome_code


@requires_postgres
class SysClaimConcurrencyTest(TransactionTestCase):

    def tearDown(self):
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()

    def active(self, resource_id):
        return ResourceLock.objects.filter(resource_type=APPT, resource_id=resource_id, status='active')

    def test_n_owners_race_exactly_one_wins(self):
        for it in range(ITERATIONS):
            rid = 10_000 + it
            codes = run_concurrently(N, lambda i: claim(i + 1, rid, f'race-{it}-{i}'))
            self.assertEqual(Counter(codes), Counter({Code.OK: 1, Code.CONFLICT: N - 1}), f'iteration {it}')
            self.assertEqual(self.active(rid).count(), 1, f'iteration {it}')
            winner = codes.index(Code.OK) + 1
            self.assertEqual(self.active(rid).get().owner_id, winner)

    def test_concurrent_retries_after_a_race(self):
        for it in range(ITERATIONS):
            rid = 20_000 + it
            first = run_concurrently(N, lambda i: claim(i + 1, rid, f'retry-{it}-{i}'))
            winner = first.index(Code.OK)
            # Everyone retries their own key at the same time.
            again = run_concurrently(N, lambda i: claim(i + 1, rid, f'retry-{it}-{i}'))
            for i, code in enumerate(again):
                expected = Code.REPLAY if i == winner else Code.CONFLICT
                self.assertEqual(code, expected, f'iteration {it}, thread {i}')
            self.assertEqual(self.active(rid).count(), 1)

    def test_same_owner_double_submit_same_key(self):
        for it in range(ITERATIONS):
            rid = 30_000 + it
            codes = run_concurrently(N, lambda i: claim(7, rid, f'dup-{it}'))
            self.assertEqual(Counter(codes), Counter({Code.OK: 1, Code.REPLAY: N - 1}), f'iteration {it}')
            self.assertEqual(self.active(rid).count(), 1)
            record = KernelIdempotencyRecord.objects.get(decision_id=f'dup-{it}')
            self.assertEqual(record.status, KernelIdempotencyRecord.STATUS_SUCCEEDED)

    def test_expired_lock_takeover_race(self):
        for it in range(ITERATIONS):
            rid = 40_000 + it
            ResourceLock.objects.create(decision_id=f'stale-{it}', resource_type=APPT, resource_id=rid,
                                        owner_id=999, expires_at=timezone.now() - timedelta(seconds=1))
            codes = run_concurrently(N, lambda i: claim(i + 1, rid, f'take-{it}-{i}'))
            self.assertEqual(Counter(codes), Counter({Code.OK: 1, Code.CONFLICT: N - 1}), f'iteration {it}')
            active = self.active(rid)
            self.assertEqual(active.count(), 1)
            self.assertEqual(active.get().owner_id, codes.index(Code.OK) + 1)
            self.assertFalse(ResourceLock.objects.filter(resource_id=rid, owner_id=999, status='active').exists())
