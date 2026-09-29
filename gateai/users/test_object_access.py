"""
M1.7 object-level access for users and peer_mock endpoints.

User A must never be able to read or change user B's data. Every endpoint acts
on request.user; these tests try to point it at B by every client-controlled
input (query params, body fields, tokens) and assert B is untouched.
"""

import io
import shutil
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache
from users.models import UserSettings

User = get_user_model()
PASSWORD_A = 'Alpha-Passw0rd!'
PASSWORD_B = 'Bravo-Passw0rd!'


class ObjectAccessBase(TestCase):
    def setUp(self):
        # Uploaded files go to a throwaway MEDIA_ROOT, never the repo's media/.
        media_root = tempfile.mkdtemp(prefix='test-media-')
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        media_override = override_settings(MEDIA_ROOT=media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.a = User.objects.create_user(username='alice', email='alice@example.com', password=PASSWORD_A)
        self.b = User.objects.create_user(username='bob', email='bob@example.com', password=PASSWORD_B,
                                          first_name='Bob', phone='555-0100', location='Boston')
        self.client_a = self.jwt(self.a)

    @staticmethod
    def jwt(user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
        return client

    def assert_b_untouched(self):
        b = User.objects.get(pk=self.b.pk)
        self.assertEqual(b.username, 'bob')
        self.assertEqual(b.email, 'bob@example.com')
        self.assertEqual(b.first_name, 'Bob')
        self.assertTrue(b.check_password(PASSWORD_B))
        self.assertFalse(b.is_staff or b.is_superuser)


class ProfileAccessTest(ObjectAccessBase):

    def test_me_ignores_attempts_to_select_another_user(self):
        for params in ({'id': self.b.pk}, {'user_id': self.b.pk}, {'pk': self.b.pk}, {'username': 'bob'}):
            with self.subTest(params=params):
                data = self.client_a.get('/api/v1/users/me/', params).json()
                self.assertEqual(data['id'], self.a.pk)
                self.assertEqual(data['username'], 'alice')
                self.assertNotIn('Boston', str(data))

    def test_me_update_cannot_target_another_user_or_escalate(self):
        response = self.client_a.put('/api/v1/users/me/', {
            'id': self.b.pk, 'user_id': self.b.pk, 'pk': self.b.pk,
            'username': 'alice2', 'email': 'alice@example.com',
            'is_staff': True, 'is_superuser': True, 'role': 'superadmin', 'email_verified': True,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        a = User.objects.get(pk=self.a.pk)
        self.assertEqual(a.username, 'alice2')
        self.assertFalse(a.is_staff or a.is_superuser)
        self.assertEqual(a.role, 'student')
        self.assertFalse(a.email_verified)
        self.assert_b_untouched()

    def test_me_update_cannot_take_another_users_username_or_email(self):
        for field, value in (('username', 'bob'), ('email', 'bob@example.com')):
            with self.subTest(field=field):
                body = {'username': 'alice', 'email': 'alice@example.com', field: value}
                response = self.client_a.put('/api/v1/users/me/', body, format='json')
                self.assertEqual(response.status_code, 400, response.content)
                self.assert_b_untouched()

    def test_username_can_change_only_once_per_90_days(self):
        first = self.client_a.put('/api/v1/users/me/', {'username': 'alice2', 'email': 'alice@example.com'}, format='json')
        self.assertEqual(first.status_code, 200, first.content)
        self.assertIsNotNone(User.objects.get(pk=self.a.pk).username_updated_at)
        second = self.client_a.put('/api/v1/users/me/', {'username': 'alice3', 'email': 'alice@example.com'}, format='json')
        self.assertEqual(second.status_code, 400, second.content)
        self.assertEqual(User.objects.get(pk=self.a.pk).username, 'alice2')

    def test_username_change_status_is_about_caller(self):
        User.objects.filter(pk=self.b.pk).update(username_updated_at=timezone.now())
        data = self.client_a.get('/api/v1/users/username-change-status/').json()
        self.assertTrue(data['can_change'])  # B is locked, A is not


class SettingsAccessTest(ObjectAccessBase):

    def test_settings_are_per_user(self):
        UserSettings.objects.create(user=self.b, data={'secret_pref': 'bob-only'})
        self.assertNotIn('bob-only', str(self.client_a.get('/api/v1/users/settings/').json()))

        response = self.client_a.put('/api/v1/users/settings/', {'theme': 'dark', 'user': self.b.pk}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(UserSettings.objects.get(user=self.b).data, {'secret_pref': 'bob-only'})


class PasswordAccessTest(ObjectAccessBase):

    def test_change_password_checks_callers_old_password(self):
        response = self.client_a.post('/api/v1/users/change-password/', {
            'username': 'bob', 'user_id': self.b.pk,
            'old_password': PASSWORD_B, 'new_password': 'Charlie-Passw0rd!', 'new_password_confirm': 'Charlie-Passw0rd!',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assert_b_untouched()

    def test_change_password_only_changes_caller(self):
        response = self.client_a.post('/api/v1/users/change-password/', {
            'user_id': self.b.pk, 'old_password': PASSWORD_A,
            'new_password': 'Charlie-Passw0rd!', 'new_password_confirm': 'Charlie-Passw0rd!',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(User.objects.get(pk=self.a.pk).check_password('Charlie-Passw0rd!'))
        self.assert_b_untouched()

    def test_reset_with_unknown_token_changes_nobody(self):
        for url, body in (
            (f'/api/v1/users/reset-password/{uuid.uuid4()}/', {}),
            ('/api/v1/users/password-reset/confirm/', {'token': str(uuid.uuid4())}),
        ):
            with self.subTest(url=url):
                body = {**body, 'email': 'bob@example.com', 'user_id': self.b.pk,
                        'new_password': 'Mallory-Passw0rd!', 'new_password_confirm': 'Mallory-Passw0rd!',
                        'password': 'Mallory-Passw0rd!', 'password2': 'Mallory-Passw0rd!'}
                response = APIClient().post(url, body, format='json')
                self.assertEqual(response.status_code, 400)
                self.assert_b_untouched()

    def test_reset_token_only_resets_its_owner(self):
        token = uuid.uuid4()
        User.objects.filter(pk=self.a.pk).update(password_reset_token=token, password_reset_sent_at=timezone.now())
        body = {'token': str(token), 'email': 'bob@example.com', 'user_id': self.b.pk,
                'new_password': 'Delta-Passw0rd!', 'new_password_confirm': 'Delta-Passw0rd!',
                'password': 'Delta-Passw0rd!', 'password2': 'Delta-Passw0rd!'}
        response = APIClient().post('/api/v1/users/password-reset/confirm/', body, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(User.objects.get(pk=self.a.pk).check_password('Delta-Passw0rd!'))
        self.assert_b_untouched()


class EmailVerificationAccessTest(ObjectAccessBase):

    def test_verification_token_only_verifies_its_owner(self):
        a = User.objects.get(pk=self.a.pk)
        a.email_verification_sent_at = timezone.now()
        a.save(update_fields=['email_verification_sent_at'])
        response = APIClient().post('/api/v1/users/verify-email/', {
            'token': str(a.email_verification_token), 'email': 'bob@example.com', 'user_id': self.b.pk,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(User.objects.get(pk=self.a.pk).email_verified)
        self.assertFalse(User.objects.get(pk=self.b.pk).email_verified)


class AvatarAccessTest(ObjectAccessBase):

    def test_avatar_upload_only_changes_caller(self):
        buf = io.BytesIO()
        Image.new('RGB', (1, 1)).save(buf, format='PNG')
        upload = SimpleUploadedFile('a.png', buf.getvalue(), content_type='image/png')
        response = self.client_a.post('/api/v1/users/avatar/', {'avatar': upload, 'user_id': self.b.pk},
                                      format='multipart')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(User.objects.get(pk=self.a.pk).avatar)
        self.assertFalse(User.objects.get(pk=self.b.pk).avatar)


class DashboardAccessTest(ObjectAccessBase):

    def test_dashboard_counts_only_callers_data(self):
        from ats_signals.models import Resume
        Resume.objects.create(user=self.b, title='bob cv', file_size=8,
                              file=SimpleUploadedFile('bob.pdf', b'%PDF-1.4', content_type='application/pdf'))
        data = self.client_a.get('/api/v1/users/dashboard/stats/', {'user_id': self.b.pk}).json()
        self.assertEqual(data['stats']['resumesUploaded'], 0)


class PeerMockAccessTest(ObjectAccessBase):
    """peer_mock is a stub today; this pins that nothing leaks across users.
    Real per-object tests must be added with the peer_mock models."""

    def setUp(self):
        super().setUp()
        BusPowerState.objects.bulk_create(
            [BusPowerState(bus_name=n, state=s) for n, s in {**BUS_POWER_DEFAULTS, 'PEER_MOCK_BUS': 'ON'}.items()])
        invalidate_cache()
        self.addCleanup(invalidate_cache)
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=['PEER_MOCK'], frozen_modules=[], reason='t')
        FeatureFlag.objects.create(key='PEER_MOCK', state='ON', visibility='user', reason='t')

    def test_endpoints_require_auth_and_return_no_other_user_data(self):
        for path in ('/api/v1/peer-mock/health/', '/api/v1/peer-mock/status/', '/api/v1/peer-mock/sessions/'):
            with self.subTest(path=path):
                self.assertEqual(APIClient().get(path).status_code, 401)
                response = self.client_a.get(path, {'user_id': self.b.pk})
                self.assertEqual(response.status_code, 200, response.content)
                self.assertNotIn('bob', str(response.content))
