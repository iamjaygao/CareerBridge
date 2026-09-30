"""
Real concurrency tests (PostgreSQL; design doc §8.3). Skipped on SQLite.

I1: N users use the last slot of an invite code at the same instant; exactly
one onboards. Also: one user submitting availability from N requests at once
ends up with exactly one registration.
"""

from collections import Counter

from django.test import TransactionTestCase

from kernel.policies.bus_power import invalidate_cache
from kernel.tests.concurrency import ITERATIONS, requires_postgres, run_concurrently
from peer_mock.models import InviteCode, PeerProfile, Registration

from .helpers import client_for, make_invite, make_round, make_user, onboard, onboarding_body, power_peer_mock

N = 5


@requires_postgres
class InviteCodeConcurrencyTest(TransactionTestCase):

    def setUp(self):
        power_peer_mock()
        self.addCleanup(invalidate_cache)

    def test_i1_last_slot_is_used_exactly_once(self):
        for it in range(ITERATIONS):
            invite, code = make_invite(f'it{it}', max_uses=1)
            clients = [client_for(make_user(f'u{it}x{i}')) for i in range(N)]
            codes = run_concurrently(N, lambda i: clients[i].put(
                '/api/v1/peer-mock/me/profile/', onboarding_body(invite_code=code), format='json').status_code)
            self.assertEqual(Counter(codes), Counter({201: 1, 400: N - 1}), f'iteration {it}')
            self.assertEqual(InviteCode.objects.get(pk=invite.pk).uses, 1)
            self.assertEqual(PeerProfile.objects.filter(invite_code=invite).count(), 1)


@requires_postgres
class RegistrationConcurrencyTest(TransactionTestCase):

    def setUp(self):
        power_peer_mock()
        self.addCleanup(invalidate_cache)

    def test_parallel_submissions_by_one_user_leave_one_registration(self):
        from .helpers import frozen
        rnd = make_round()
        url = f'/api/v1/peer-mock/rounds/{rnd.public_id}/registration/'
        for it in range(ITERATIONS):
            user = make_user(f'r{it}')
            onboard(user)
            client = client_for(user)
            body = {'interview_type': 'coding', 'direction': 'backend',
                    'windows': [{'date': '2026-11-03', 'start': '18:00', 'end': '20:00'}]}
            with frozen():
                codes = run_concurrently(N, lambda i: client.put(url, body, format='json').status_code)
            self.assertEqual(Counter(codes), Counter({200: N}), f'iteration {it}')
            registration = Registration.objects.get(round=rnd, user=user)
            self.assertEqual(registration.windows.count(), 1)
