"""
gateai.settings picks dev or prod settings from DJANGO_ENV. It must refuse to
guess: an unset or unknown DJANGO_ENV is an error, never a silent fallback to
the development settings (hardcoded SECRET_KEY, DEBUG=True).
"""

import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

PROD_ENV = {
    'SECRET_KEY': 'test-only-not-a-real-key',
    'ALLOWED_HOSTS': 'example.com',
    'CORS_ALLOWED_ORIGINS': 'https://example.com',
    'CSRF_TRUSTED_ORIGINS': 'https://example.com',
    'DATABASE_URL': 'postgresql://app:pw@db:5432/app',
    # Fake SMTP settings (required by settings_prod since M3; never used to send).
    'EMAIL_HOST': 'smtp.example.invalid',
    'EMAIL_PORT': '587',
    'EMAIL_HOST_USER': 'test',
    'EMAIL_HOST_PASSWORD': 'test-only-not-real',
    'EMAIL_USE_TLS': 'true',
    'DEFAULT_FROM_EMAIL': 'test@example.invalid',
}


def load_router(extra_env):
    code = ('import django; django.setup(); from django.conf import settings; '
            'print("DEBUG=" + str(settings.DEBUG))')
    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=str(Path(settings.BASE_DIR)),
        env={'PATH': '/usr/bin:/bin', 'DJANGO_SETTINGS_MODULE': 'gateai.settings', **extra_env},
        capture_output=True, text=True, timeout=60,
    )


class SettingsRouterTest(SimpleTestCase):

    def test_unset_django_env_is_an_error(self):
        result = load_router({})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('DJANGO_ENV', result.stderr)

    def test_unknown_django_env_is_an_error(self):
        for value in ('prod', 'dev', 'staging', ''):
            with self.subTest(value=value):
                result = load_router({'DJANGO_ENV': value})
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('DJANGO_ENV', result.stderr)

    def test_development_and_test_load_dev_settings(self):
        for value in ('development', 'test'):
            with self.subTest(value=value):
                result = load_router({'DJANGO_ENV': value})
                self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                self.assertIn('DEBUG=True', result.stdout)

    def test_production_loads_prod_settings(self):
        result = load_router({'DJANGO_ENV': 'production', **PROD_ENV})
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn('DEBUG=False', result.stdout)
