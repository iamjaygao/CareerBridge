"""The peer_mock models and migrations agree (makemigrations --check)."""

import unittest

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

_modules = getattr(settings, 'MIGRATION_MODULES', {})
MIGRATIONS_DISABLED = 'peer_mock' in _modules and _modules['peer_mock'] is None


@unittest.skipIf(MIGRATIONS_DISABLED, 'migrations are disabled in these settings; runs in backend-postgres')
class MigrationsUpToDateTest(SimpleTestCase):

    def test_no_missing_migrations(self):
        try:
            call_command('makemigrations', 'peer_mock', '--check', '--dry-run', verbosity=0)
        except SystemExit:
            self.fail('peer_mock models have changes without a migration')
