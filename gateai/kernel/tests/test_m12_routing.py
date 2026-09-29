"""
M1.2 routing and governance decisions.

- Only one kernel mount exists: /api/v1/kernel/ (the one the SPA calls).
- Legacy notifications/resumes redirects and the unsigned PayPal webhook are gone.
- Every area maps to an explicit bus.
- Feature-flag visibility and BETA are enforced for JWT users (by DRF), and a
  flag change is seen by the next request even if made by another process.
"""

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache, resolve_bus

User = get_user_model()


def assert_not_routed(test, path):
    with test.assertRaises(Resolver404, msg=f'{path} should not be routed'):
        resolve(path)


class RouteRemovalTest(SimpleTestCase):

    def test_only_api_v1_kernel_mount_exists(self):
        for path in ('/kernel/dispatch', '/kernel/observability/audit', '/kernel/console/buses/',
                     '/kernel/pulse/summary/'):
            with self.subTest(path=path):
                assert_not_routed(self, path)
        for path in ('/api/v1/kernel/dispatch', '/api/v1/kernel/observability/audit',
                     '/api/v1/kernel/console/buses/', '/api/v1/kernel/pulse/summary/'):
            with self.subTest(path=path):
                resolve(path)

    def test_legacy_redirects_removed(self):
        for path in ('/api/v1/notifications/', '/api/v1/resumes/'):
            with self.subTest(path=path):
                assert_not_routed(self, path)

    def test_paypal_webhook_removed_stripe_kept(self):
        assert_not_routed(self, '/api/v1/payments/webhooks/paypal/')
        resolve('/api/v1/payments/webhooks/stripe/')


class BusMappingTest(SimpleTestCase):

    def test_bus_assignments(self):
        expected = {
            '/api/v1/users/register/': 'KERNEL_CORE_BUS',
            '/api/v1/users/me/': 'KERNEL_CORE_BUS',
            '/api/v1/adminpanel/governance/platform-state/': 'KERNEL_CORE_BUS',
            '/api/v1/kernel/observability/audit': 'KERNEL_CORE_BUS',
            '/api/v1/adminpanel/users/': 'ADMIN_BUS',
            '/api/v1/ping/': 'PUBLIC_WEB_BUS',
            '/api/info/': 'PUBLIC_WEB_BUS',
            '/api/v1/': 'PUBLIC_WEB_BUS',
            '/api/v1/peer-mock/status/': 'PEER_MOCK_BUS',
        }
        for path, bus in expected.items():
            with self.subTest(path=path):
                self.assertEqual(resolve_bus(path), bus)


def seed_buses(**overrides):
    BusPowerState.objects.all().delete()
    BusPowerState.objects.bulk_create(
        [BusPowerState(bus_name=n, state=s) for n, s in {**BUS_POWER_DEFAULTS, **overrides}.items()]
    )
    invalidate_cache()


class FeatureVisibilityForJwtUsersTest(TestCase):
    URL = '/api/v1/peer-mock/status/'

    def setUp(self):
        seed_buses(PEER_MOCK_BUS='ON')
        self.addCleanup(invalidate_cache)
        self.superuser = User.objects.create_user(
            username='root', email='root@example.com', password='pw', is_superuser=True, is_staff=True)
        self.staff = User.objects.create_user(username='staff', email='staff@example.com', password='pw', is_staff=True)
        self.regular = User.objects.create_user(username='reg', email='reg@example.com', password='pw')
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[],
                                     reason='t', updated_by=self.superuser)
        self.flag = FeatureFlag.objects.create(key='PEER_MOCK', state='ON', visibility='user',
                                               reason='t', updated_by=self.superuser)

    def status_for(self, user):
        client = APIClient()
        if user is not None:
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
        return client.get(self.URL).status_code

    def set_flag(self, state, visibility):
        FeatureFlag.objects.filter(pk=self.flag.pk).update(state=state, visibility=visibility)

    def test_user_visibility(self):
        self.assertEqual(self.status_for(None), 401)
        self.assertEqual(self.status_for(self.regular), 200)

    def test_staff_visibility(self):
        self.set_flag('ON', 'staff')
        self.assertEqual(self.status_for(self.regular), 404)
        self.assertEqual(self.status_for(self.staff), 200)
        self.assertEqual(self.status_for(self.superuser), 200)

    def test_internal_visibility(self):
        self.set_flag('ON', 'internal')
        self.assertEqual(self.status_for(self.regular), 404)
        self.assertEqual(self.status_for(self.staff), 404)
        self.assertEqual(self.status_for(self.superuser), 200)

    def test_beta_is_superuser_only(self):
        self.set_flag('BETA', 'user')
        self.assertEqual(self.status_for(self.regular), 404)
        self.assertEqual(self.status_for(self.staff), 404)
        self.assertEqual(self.status_for(self.superuser), 200)

    def test_off_hides_from_everyone(self):
        self.set_flag('OFF', 'user')
        for user in (None, self.regular, self.staff, self.superuser):
            with self.subTest(user=getattr(user, 'username', 'anonymous')):
                self.assertEqual(self.status_for(user), 404)

    def test_flag_change_by_another_process_seen_by_next_request(self):
        self.assertEqual(self.status_for(self.regular), 200)  # warms any cache
        self.set_flag('OFF', 'user')                         # no invalidation call
        self.assertEqual(self.status_for(self.regular), 404)
        self.set_flag('ON', 'user')
        self.assertEqual(self.status_for(self.regular), 200)
