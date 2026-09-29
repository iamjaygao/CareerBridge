"""
settings_prod must fail loudly when a secret is missing, never fall back.

Each case imports settings_prod in a fresh interpreter with a controlled
environment, so nothing from the test process leaks in.
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


def load_prod_settings(env):
    code = (
        'import django; django.setup(); from django.conf import settings; '
        'print("DB_PASSWORD_SET=" + str(bool(settings.DATABASES["default"]["PASSWORD"])))'
    )
    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=str(Path(settings.BASE_DIR)),
        env={'PATH': '/usr/bin:/bin', **env},
        capture_output=True, text=True, timeout=60,
    )


class ProdSettingsFailLoudTest(SimpleTestCase):

    def assert_refuses(self, env, needle):
        result = load_prod_settings(env)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(needle, result.stderr)

    def test_complete_env_loads(self):
        # Control case: proves the harness can load settings_prod at all.
        result = load_prod_settings(BASE_ENV)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn('DB_PASSWORD_SET=True', result.stdout)

    def test_missing_secret_key_refuses(self):
        env = {k: v for k, v in BASE_ENV.items() if k != 'SECRET_KEY'}
        self.assert_refuses(env, 'SECRET_KEY')

    def test_database_url_without_password_refuses(self):
        # docker-compose builds DATABASE_URL from ${POSTGRES_PASSWORD}; when that
        # is unset the URL has an empty password.
        env = {**BASE_ENV, 'DATABASE_URL': 'postgresql://app:@db:5432/app'}
        self.assert_refuses(env, 'password')

    def test_missing_postgres_password_refuses(self):
        env = {k: v for k, v in BASE_ENV.items() if k != 'DATABASE_URL'}
        env.update({'POSTGRES_DB': 'app', 'POSTGRES_USER': 'app'})
        self.assert_refuses(env, 'POSTGRES_PASSWORD')
