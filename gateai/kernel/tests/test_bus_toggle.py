"""
Bus power switch: who may toggle it, what it records, and when it takes effect.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from kernel.governance.models import BusPowerState, GovernanceAudit
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

User = get_user_model()

TOGGLE_URLS = ['/api/v1/kernel/console/buses/']  # the only kernel mount
ADMIN_URL = '/admin/'


def seed_buses(**overrides):
    BusPowerState.objects.all().delete()
    states = {**BUS_POWER_DEFAULTS, **overrides}
    BusPowerState.objects.bulk_create(
        [BusPowerState(bus_name=name, state=state) for name, state in states.items()]
    )
    invalidate_cache()


class BusToggleTestBase(TestCase):
    def setUp(self):
        seed_buses()
        self.addCleanup(invalidate_cache)
        self.superuser = User.objects.create_user(
            username='root', email='root@example.com', password='pw', is_superuser=True, is_staff=True,
        )
        self.staff = User.objects.create_user(
            username='staff', email='staff@example.com', password='pw', is_staff=True,
        )
        self.regular = User.objects.create_user(
            username='regular', email='regular@example.com', password='pw',
        )

    def jwt_client(self, user=None):
        client = APIClient()
        if user is not None:
            token = RefreshToken.for_user(user).access_token
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def session_client(self, user=None):
        client = Client()
        if user is not None:
            client.force_login(user)
        return client

    def admin_bus_state(self):
        return BusPowerState.objects.get(bus_name='ADMIN_BUS').state


class BusTogglePermissionTest(BusToggleTestBase):

    def test_anonymous_gets_401(self):
        for url in TOGGLE_URLS:
            with self.subTest(url=url):
                response = self.jwt_client().patch(url, {'ADMIN_BUS': 'ON'}, format='json')
                self.assertEqual(response.status_code, 401)
                self.assertEqual(self.admin_bus_state(), 'OFF')

    def test_regular_user_and_staff_get_403(self):
        for url in TOGGLE_URLS:
            for user in (self.regular, self.staff):
                with self.subTest(url=url, user=user.username):
                    response = self.jwt_client(user).patch(url, {'ADMIN_BUS': 'ON'}, format='json')
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.admin_bus_state(), 'OFF')

    def test_superuser_can_toggle(self):
        for url in TOGGLE_URLS:
            with self.subTest(url=url):
                seed_buses()
                response = self.jwt_client(self.superuser).patch(url, {'ADMIN_BUS': 'ON'}, format='json')
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(self.admin_bus_state(), 'ON')


class BusToggleAuditTest(BusToggleTestBase):

    def test_toggle_writes_bus_specific_audit_entry(self):
        client = self.jwt_client(self.superuser)
        for new_state, action in (('ON', 'BUS_ENABLE'), ('OFF', 'BUS_DISABLE')):
            with self.subTest(new_state=new_state):
                old_state = self.admin_bus_state()
                response = client.patch(TOGGLE_URLS[0], {'ADMIN_BUS': new_state}, format='json')
                self.assertEqual(response.status_code, 200, response.content)

                entry = GovernanceAudit.objects.order_by('-created_at').first()
                self.assertEqual(entry.action, action)
                self.assertEqual(entry.actor, self.superuser)
                self.assertIsNotNone(entry.created_at)
                self.assertEqual(entry.payload['bus'], 'ADMIN_BUS')
                self.assertEqual(entry.payload['old_state'], old_state)
                self.assertEqual(entry.payload['new_state'], new_state)


class BusToggleTakesEffectTest(BusToggleTestBase):

    def test_toggle_via_api_seen_by_next_request(self):
        admin = self.session_client(self.staff)
        self.assertEqual(admin.get(ADMIN_URL).status_code, 404)

        response = self.jwt_client(self.superuser).patch(TOGGLE_URLS[0], {'ADMIN_BUS': 'ON'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(admin.get(ADMIN_URL).status_code, 200)

    def test_change_made_by_another_process_seen_by_next_request(self):
        # Another worker toggling the bus updates the row, but cannot clear this
        # process's memory. Simulate that: update the row, don't invalidate.
        admin = self.session_client(self.staff)
        self.assertEqual(admin.get(ADMIN_URL).status_code, 404)  # warms any cache

        BusPowerState.objects.filter(bus_name='ADMIN_BUS').update(state='ON')

        self.assertEqual(admin.get(ADMIN_URL).status_code, 200)


class AdminBusGatesDjangoAdminTest(BusToggleTestBase):

    def test_admin_bus_off_hides_admin_from_everyone(self):
        seed_buses(ADMIN_BUS='OFF')
        for user in (None, self.regular, self.staff, self.superuser):
            name = user.username if user else 'anonymous'
            with self.subTest(user=name):
                response = self.session_client(user).get(ADMIN_URL)
                self.assertEqual(response.status_code, 404)

    def test_admin_bus_on_still_requires_staff(self):
        seed_buses(ADMIN_BUS='ON')
        for user in (None, self.regular):
            name = user.username if user else 'anonymous'
            with self.subTest(user=name):
                response = self.session_client(user).get(ADMIN_URL)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/admin/login/', response['Location'])
        for user in (self.staff, self.superuser):
            with self.subTest(user=user.username):
                self.assertEqual(self.session_client(user).get(ADMIN_URL).status_code, 200)
