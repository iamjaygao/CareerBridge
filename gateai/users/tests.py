from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from adminpanel.permissions import is_superadmin

User = get_user_model()

REGISTER_URL = '/api/v1/users/register/'
DEFAULT_ROLE = 'student'


class RegisterRoleAssignmentTest(TestCase):
    """Signup must never let the client choose a role or privilege flags."""

    def setUp(self):
        self.client = APIClient()

    def _register(self, n, **extra):
        payload = {
            'username': f'signup{n}',
            'email': f'signup{n}@example.com',
            'first_name': 'Sign',
            'last_name': 'Up',
            'password': 'Str0ng-Passw0rd!',
            'password2': 'Str0ng-Passw0rd!',
        }
        payload.update(extra)
        return self.client.post(REGISTER_URL, payload, format='json')

    def assert_default_unprivileged(self, username):
        user = User.objects.get(username=username)
        self.assertEqual(user.role, DEFAULT_ROLE)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_client_supplied_role_is_ignored(self):
        for n, role in enumerate(['superadmin', 'admin', 'staff', 'mentor']):
            with self.subTest(role=role):
                response = self._register(n, role=role)
                self.assertEqual(response.status_code, 201, response.content)
                self.assert_default_unprivileged(f'signup{n}')

    def test_client_supplied_privilege_flags_are_ignored(self):
        response = self._register(10, is_superuser=True, is_staff=True, role='superadmin')
        self.assertEqual(response.status_code, 201, response.content)
        self.assert_default_unprivileged('signup10')

    def test_register_without_role_gets_default(self):
        response = self._register(20)
        self.assertEqual(response.status_code, 201, response.content)
        self.assert_default_unprivileged('signup20')


class RoleFlagDecouplingTest(TestCase):
    """The role string is application data; it must not grant Django privilege flags."""

    def test_privileged_role_does_not_set_flags(self):
        for role in ['superadmin', 'admin', 'staff']:
            with self.subTest(role=role):
                user = User.objects.create_user(
                    username=f'r_{role}', email=f'r_{role}@example.com', password='x', role=role,
                )
                user.refresh_from_db()
                self.assertFalse(user.is_superuser)
                self.assertFalse(user.is_staff)

    def test_changing_role_later_does_not_set_flags(self):
        user = User.objects.create_user(username='later', email='later@example.com', password='x')
        user.role = 'superadmin'
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_superadmin_role_string_alone_is_not_superadmin(self):
        user = User.objects.create_user(
            username='fake', email='fake@example.com', password='x', role='superadmin',
        )
        self.assertFalse(is_superadmin(user))


class SuperuserCreationTest(TestCase):
    """Superusers come from manage.py createsuperuser."""

    def test_createsuperuser_command_creates_superuser(self):
        call_command(
            'createsuperuser', interactive=False,
            username='root', email='root@example.com', verbosity=0,
        )
        user = User.objects.get(username='root')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, 'superadmin')
        self.assertTrue(is_superadmin(user))
