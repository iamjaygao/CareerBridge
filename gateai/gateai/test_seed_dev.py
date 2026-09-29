"""
seed_dev.py creates a superuser with a fixed password, so it must refuse to run
anywhere that looks like production.
"""

import os
import runpy
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

SEED_SCRIPT = str(Path(settings.BASE_DIR) / 'scripts' / 'seed_dev.py')

User = get_user_model()


class SeedDevProductionGuardTest(TestCase):
    # The test runner forces DEBUG=False, so each test sets DEBUG explicitly;
    # otherwise the DEBUG check alone would make the production cases pass.

    def run_seed(self):
        runpy.run_path(SEED_SCRIPT, run_name='__main__')

    def assert_refused(self):
        with self.assertRaises((SystemExit, RuntimeError)) as ctx:
            self.run_seed()
        if isinstance(ctx.exception, SystemExit):
            self.assertNotIn(ctx.exception.code, (0, None))
        self.assertFalse(User.objects.exists(), 'seed_dev wrote users before refusing')

    @override_settings(DEBUG=True)  # a misconfigured prod must still be refused
    def test_refuses_when_django_env_is_production(self):
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'production'}):
            self.assert_refused()

    @override_settings(DEBUG=True)  # a misconfigured prod must still be refused
    def test_refuses_under_prod_settings_module(self):
        with mock.patch.dict(os.environ, {'DJANGO_SETTINGS_MODULE': 'gateai.settings_prod'}):
            self.assert_refused()

    @override_settings(DEBUG=False)
    def test_refuses_when_debug_is_off(self):
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'development'}):
            self.assert_refused()

    @override_settings(DEBUG=True)
    def test_runs_in_development(self):
        # Guards against a vacuous guard test: in dev the script does seed.
        with mock.patch.dict(os.environ, {'DJANGO_ENV': 'development'}):
            self.run_seed()
        self.assertTrue(User.objects.filter(username='admin', is_superuser=True).exists())
