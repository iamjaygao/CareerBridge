"""
Login flow, end to end through the middleware, as a governance-initialised
production deployment has it (USERS flag ON, visibility 'user').
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from kernel.governance.models import FeatureFlag, PlatformState

User = get_user_model()
LOGIN = '/api/v1/users/login/'
REFRESH = '/api/v1/users/refresh/'
ME = '/api/v1/users/me/'
PASSWORD = 'Login-Passw0rd!'


class LoginFlowTest(TestCase):

    def setUp(self):
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[], reason='t')
        FeatureFlag.objects.create(key='USERS', state='ON', visibility='user', reason='t')
        self.user = User.objects.create_user(username='carol', email='Carol@Example.com', password=PASSWORD)
        self.client = APIClient()

    def login(self, identifier, password=PASSWORD):
        return self.client.post(LOGIN, {'identifier': identifier, 'password': password}, format='json')

    def test_login_with_username_returns_working_tokens(self):
        response = self.login('carol')
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body['user']['username'], 'carol')
        self.assertNotIn('password', body['user'])

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        self.assertEqual(client.get(ME).json()['username'], 'carol')

    def test_login_with_email_is_case_insensitive(self):
        for identifier in ('Carol@Example.com', 'carol@example.com', 'CAROL@EXAMPLE.COM'):
            with self.subTest(identifier=identifier):
                self.assertEqual(self.login(identifier).status_code, 200)

    def test_refresh_token_issues_a_new_access_token(self):
        refresh = self.login('carol').json()['refresh']
        response = self.client.post(REFRESH, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn('access', response.json())

    def test_wrong_password_and_unknown_account_look_the_same(self):
        wrong = self.login('carol', 'not-the-password')
        unknown = self.login('nobody@example.com', 'not-the-password')
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(wrong.json(), unknown.json(), 'responses must not reveal which accounts exist')
        self.assertNotIn('access', wrong.json())

    def test_inactive_user_cannot_log_in(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        response = self.login('carol')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('access', response.json())

    def test_missing_fields_are_rejected(self):
        for body in ({}, {'identifier': 'carol'}, {'password': PASSWORD}, {'identifier': '', 'password': ''}):
            with self.subTest(body=body):
                response = self.client.post(LOGIN, body, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertNotIn('access', response.json())

    def test_garbage_refresh_token_is_rejected(self):
        response = self.client.post(REFRESH, {'refresh': 'not.a.token'}, format='json')
        self.assertEqual(response.status_code, 401)
