"""
M2 sys_claim semantics (sequential; run on SQLite and Postgres).

Idempotency contract (per idempotency key = decision_id + context_hash):
- The winner retrying the same key gets REPLAY (HTTP 200) for the same lock.
- A loser retrying the same key gets CONFLICT (HTTP 409), never REPLAY.
- The same key presented by a different owner is refused (CONFLICT, 409).
Physical contract (per resource):
- At most one *active* lock per (resource_type, resource_id), enforced by a
  partial unique constraint; released/expired rows don't block re-locking.
- A conflict caught inside a caller's transaction uses a savepoint, so the
  caller's transaction stays usable.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from decision_slots.models import ResourceLock
from kernel.abi import KernelOutcomeCode
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
from kernel.syscalls import sys_claim

APPT = ResourceLock.RESOURCE_TYPE_APPOINTMENT


def claim(owner, resource_id=1, decision='d', ctx='c', seconds=600):
    return sys_claim({
        'decision_id': decision, 'context_hash': ctx, 'resource_type': APPT,
        'resource_id': resource_id, 'owner_id': owner, 'duration_seconds': seconds,
    })


class SysClaimSemanticsBase(TransactionTestCase):
    def tearDown(self):
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()

    def active_locks(self, resource_id=1):
        return ResourceLock.objects.filter(resource_type=APPT, resource_id=resource_id, status='active')


class RetrySemanticsTest(SysClaimSemanticsBase):

    def test_winner_retry_same_key_is_idempotent(self):
        first = claim(owner=1, decision='win', ctx='k')
        self.assertEqual(first.outcome_code, KernelOutcomeCode.OK)
        retry = claim(owner=1, decision='win', ctx='k')
        self.assertEqual(retry.outcome_code, KernelOutcomeCode.REPLAY)
        self.assertEqual(retry.outcome['extras'].get('lock_id'), first.outcome['extras']['lock_id'])
        self.assertEqual(self.active_locks().count(), 1)

    def test_loser_retry_same_key_gets_conflict_not_replay(self):
        self.assertEqual(claim(owner=1, decision='a', ctx='k').outcome_code, KernelOutcomeCode.OK)
        lost = claim(owner=2, decision='b', ctx='k')
        self.assertEqual(lost.outcome_code, KernelOutcomeCode.CONFLICT)
        for _ in range(3):
            retry = claim(owner=2, decision='b', ctx='k')
            self.assertEqual(retry.outcome_code, KernelOutcomeCode.CONFLICT)
        self.assertEqual(list(self.active_locks().values_list('owner_id', flat=True)), [1])

    def test_same_key_presented_by_different_owner_is_refused(self):
        self.assertEqual(claim(owner=1, decision='shared', ctx='k').outcome_code, KernelOutcomeCode.OK)
        other = claim(owner=3, decision='shared', ctx='k')
        self.assertEqual(other.outcome_code, KernelOutcomeCode.CONFLICT)
        self.assertEqual(list(self.active_locks().values_list('owner_id', flat=True)), [1])

    def test_idempotency_record_reaches_a_final_state(self):
        claim(owner=1, decision='a', ctx='k')
        claim(owner=2, decision='b', ctx='k')
        records = dict(KernelIdempotencyRecord.objects.values_list('decision_id', 'status'))
        self.assertEqual(records['a'], KernelIdempotencyRecord.STATUS_SUCCEEDED)
        self.assertEqual(records['b'], KernelIdempotencyRecord.STATUS_REJECTED)

    def test_owner_is_stored(self):
        result = claim(owner=42)
        self.assertEqual(result.outcome_code, KernelOutcomeCode.OK)
        self.assertEqual(self.active_locks().get().owner_id, 42)


class DispatchHttpStatusTest(SysClaimSemanticsBase):

    def test_loser_retry_is_http_409(self):
        root = get_user_model().objects.create_user(
            username='root', email='root@example.com', password='pw', is_superuser=True, is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(root).access_token}')

        def dispatch(owner, decision):
            return client.post('/api/v1/kernel/dispatch', {'syscall_name': 'sys_claim', 'payload': {
                'decision_id': decision, 'context_hash': 'k', 'resource_type': APPT,
                'resource_id': 7, 'owner_id': owner, 'duration_seconds': 600}}, format='json')

        self.assertEqual(dispatch(1, 'a').status_code, 200)
        self.assertEqual(dispatch(2, 'b').status_code, 409)
        self.assertEqual(dispatch(2, 'b').status_code, 409)  # retry
        self.assertEqual(dispatch(1, 'a').status_code, 200)  # winner replay


class SavepointTest(SysClaimSemanticsBase):

    def test_conflict_inside_caller_transaction_keeps_it_usable(self):
        ResourceLock.objects.create(decision_id='held', resource_type=APPT, resource_id=9,
                                    owner_id=99, expires_at=timezone.now() + timedelta(hours=1))
        with transaction.atomic():
            result = claim(owner=1, resource_id=9, decision='mine', ctx='k')
            self.assertEqual(result.outcome_code, KernelOutcomeCode.CONFLICT)
            # The transaction is not aborted: reads and writes still work.
            self.assertEqual(self.active_locks(9).count(), 1)
            ResourceLock.objects.create(decision_id='after', resource_type=APPT, resource_id=10,
                                        owner_id=1, expires_at=timezone.now() + timedelta(hours=1))
        # ...and it committed.
        self.assertTrue(ResourceLock.objects.filter(decision_id='after').exists())

    def test_success_inside_caller_transaction_rolls_back_with_it(self):
        class Boom(Exception):
            pass
        with self.assertRaises(Boom):
            with transaction.atomic():
                self.assertEqual(claim(owner=1, resource_id=11).outcome_code, KernelOutcomeCode.OK)
                raise Boom()
        self.assertFalse(self.active_locks(11).exists())


class PartialUniqueConstraintTest(SysClaimSemanticsBase):

    def make(self, status, owner=1):
        return ResourceLock.objects.create(decision_id=f'x-{status}-{owner}', resource_type=APPT, resource_id=20,
                                           owner_id=owner, status=status,
                                           expires_at=timezone.now() + timedelta(hours=1))

    def test_inactive_rows_do_not_block_a_new_active_lock(self):
        self.make('released')
        self.make('expired', owner=2)
        self.make('active', owner=3)
        self.assertEqual(self.active_locks(20).count(), 1)

    def test_second_active_lock_is_rejected_by_the_database(self):
        self.make('active')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make('active', owner=2)
