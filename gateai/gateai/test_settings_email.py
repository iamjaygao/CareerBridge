"""
Production email is generic SMTP configured entirely from the environment.
Every setting is required; a missing or malformed value stops startup.
"""

import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

BASE_ENV = {
    'DJANGO_SETTINGS_MODULE': 'gateai.settings_prod',
    'SECRET_KEY': 'test-only-not-a-real-key',
    'ALLOWED_HOSTS': 'example.com',
    'CORS_ALLOWED_ORIGINS': 'https://example.com',
    'CSRF_TRUSTED_ORIGINS': 'https://example.com',
    'DATABASE_URL': 'postgresql://app:pw@db:5432/app',
}
EMAIL_ENV = {
    'EMAIL_HOST': 'smtp.example.com',
    'EMAIL_PORT': '587',
    'EMAIL_HOST_USER': 'mailer',
    'EMAIL_HOST_PASSWORD': 'test-only-password',
    'EMAIL_USE_TLS': 'true',
    'DEFAULT_FROM_EMAIL': 'CareerBridge <no-reply@example.com>',
}
PRINT = ('import django; django.setup(); from django.conf import settings as s; '
         'print(s.EMAIL_BACKEND, s.EMAIL_HOST, s.EMAIL_PORT, repr(s.EMAIL_USE_TLS), sep="|"); '
         'print(s.EMAIL_HOST_USER, bool(s.EMAIL_HOST_PASSWORD), s.DEFAULT_FROM_EMAIL, sep="|")')


def load(env):
    return subprocess.run([sys.executable, '-c', PRINT], cwd=str(Path(settings.BASE_DIR)),
                          env={'PATH': '/usr/bin:/bin', **env}, capture_output=True, text=True, timeout=60)


class ProdEmailSettingsTest(SimpleTestCase):

    def test_complete_email_env_configures_smtp(self):
        result = load({**BASE_ENV, **EMAIL_ENV})
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        line1, line2 = result.stdout.strip().splitlines()
        self.assertEqual(line1, 'django.core.mail.backends.smtp.EmailBackend|smtp.example.com|587|True')
        self.assertEqual(line2, 'mailer|True|CareerBridge <no-reply@example.com>')

    def test_each_missing_email_setting_refuses(self):
        for name in EMAIL_ENV:
            with self.subTest(missing=name):
                env = {**BASE_ENV, **{k: v for k, v in EMAIL_ENV.items() if k != name}}
                result = load(env)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(name, result.stderr)

    def test_malformed_values_refuse(self):
        for name, value in (('EMAIL_PORT', 'smtp'), ('EMAIL_USE_TLS', 'maybe')):
            with self.subTest(name=name, value=value):
                result = load({**BASE_ENV, **EMAIL_ENV, name: value})
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(name, result.stderr)

    def test_tls_can_be_disabled_explicitly(self):
        result = load({**BASE_ENV, **EMAIL_ENV, 'EMAIL_USE_TLS': 'false'})
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("|False", result.stdout.splitlines()[0])
