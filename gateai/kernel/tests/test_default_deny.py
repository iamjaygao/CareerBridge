"""
Default-deny access control.

- Kernel endpoints (both /kernel/ and the /api/v1/kernel/ mirror) reject
  anonymous callers with 401 and do nothing.
- JWT is honoured by DRF on every view, so a JWT superuser reaches the
  governance API and a JWT user reaches their own profile.
- A path that maps to no bus is refused, and every routed URL maps to a bus.
"""

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, SimpleTestCase
from django.urls import get_resolver
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from decision_slots.models import ResourceLock
from kernel.governance.middleware import GovernanceMiddleware
from kernel.governance.models import FeatureFlag, PlatformState
from kernel.models import KernelAuditLog
from kernel.policies.bus_power import resolve_bus

User = get_user_model()

KERNEL_PREFIXES = ['/kernel/', '/api/v1/kernel/']


def routed_paths(prefix=''):
    """Concrete paths for every URL pattern without path parameters."""
    paths = []

    def walk(patterns, acc):
        for p in patterns:
            route = acc + str(p.pattern)
            if hasattr(p, 'url_patterns'):
                walk(p.url_patterns, route)
            elif '<' not in route and '(?P' not in route and '^' not in route:
                paths.append('/' + route)

    walk(get_resolver().url_patterns, '')
    return [p for p in paths if p.startswith(prefix)]


def kernel_endpoint_paths():
    return [p for prefix in KERNEL_PREFIXES for p in routed_paths(prefix)]


def jwt_client(user=None):
    client = APIClient()
    if user is not None:
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
    return client


class KernelEndpointsRequireAuthTest(TestCase):

    def test_kernel_endpoint_inventory_is_not_empty(self):
        # Guard against the tests below passing over an empty list.
        paths = kernel_endpoint_paths()
        self.assertIn('/api/v1/kernel/observability/audit', paths)
        self.assertIn('/api/v1/kernel/dispatch', paths)
        self.assertIn('/kernel/dispatch', paths)

    def test_anonymous_gets_401_on_every_kernel_endpoint(self):
        client = jwt_client()
        for path in kernel_endpoint_paths():
            with self.subTest(path=path):
                method = client.post if path.endswith('/dispatch') else client.get
                response = method(path, {}, format='json')
                self.assertEqual(response.status_code, 401, response.content[:200])

    def test_anonymous_dispatch_changes_nothing(self):
        body = {
            'syscall_name': 'sys_claim',
            'payload': {
                'decision_id': 'anon:probe', 'context_hash': 'h', 'resource_type': 'APPOINTMENT',
                'resource_id': 1, 'owner_id': 1, 'duration_seconds': 60,
            },
        }
        for path in ('/kernel/dispatch', '/api/v1/kernel/dispatch'):
            with self.subTest(path=path):
                jwt_client().post(path, body, format='json')
                self.assertEqual(ResourceLock.objects.count(), 0)
                self.assertEqual(KernelAuditLog.objects.count(), 0)

    def test_non_superuser_gets_403_on_every_kernel_endpoint(self):
        staff = User.objects.create_user(username='staff', email='staff@example.com', password='pw', is_staff=True)
        client = jwt_client(staff)
        for path in kernel_endpoint_paths():
            with self.subTest(path=path):
                method = client.post if path.endswith('/dispatch') else client.get
                response = method(path, {}, format='json')
                self.assertEqual(response.status_code, 403, response.content[:200])


class JwtHonouredTest(TestCase):

    def setUp(self):
        self.superuser = User.objects.create_user(
            username='root', email='root@example.com', password='pw', is_superuser=True, is_staff=True,
        )
        # Governance as kernel_init_governance leaves it.
        PlatformState.objects.create(
            state='SINGLE_WORKLOAD', active_workloads=['PEER_MOCK'], frozen_modules=[],
            reason='test', updated_by=self.superuser,
        )
        FeatureFlag.objects.create(key='USERS', state='ON', visibility='user', reason='t', updated_by=self.superuser)
        FeatureFlag.objects.create(key='KERNEL_ADMIN', state='ON', visibility='internal', reason='t', updated_by=self.superuser)

    def test_jwt_superuser_reaches_governance_api(self):
        client = jwt_client(self.superuser)
        for path in ('/api/v1/adminpanel/governance/platform-state/',
                     '/api/v1/adminpanel/governance/feature-flags/'):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 200)

    def test_jwt_user_reaches_own_profile(self):
        user = User.objects.create_user(username='u', email='u@example.com', password='pw')
        response = jwt_client(user).get('/api/v1/users/me/')
        self.assertEqual(response.status_code, 200, response.content[:200])
        self.assertEqual(response.json()['username'], 'u')

    def test_anonymous_can_register_when_users_flag_is_on(self):
        response = jwt_client().post('/api/v1/users/register/', {
            'username': 'newbie', 'email': 'newbie@example.com', 'first_name': 'N', 'last_name': 'B',
            'password': 'Str0ng-Passw0rd!', 'password2': 'Str0ng-Passw0rd!',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content[:200])


class UnknownBusDeniedTest(SimpleTestCase):

    def test_request_on_unknown_bus_is_refused(self):
        path = '/api/v1/zz-no-such-area/'
        self.assertEqual(resolve_bus(path), 'UNKNOWN')
        middleware = GovernanceMiddleware(lambda request: HttpResponse('reached view', status=200))
        response = middleware(RequestFactory().get(path))
        self.assertEqual(response.status_code, 404)

    def test_every_routed_url_maps_to_a_known_bus(self):
        unknown = sorted({p for p in routed_paths() if resolve_bus(p) == 'UNKNOWN'})
        self.assertEqual(unknown, [], 'routes with no bus would be refused')
