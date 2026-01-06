"""
Test-only Django settings for GateAI kernel tests.

IMPORTANT: This file is ONLY used during test execution to provide:
- Isolated in-memory SQLite database (deterministic + fast)
- Disabled migrations (bypasses historical migration pollution)

This MUST NOT be used in development or production environments.
"""

# Import all base settings
from .settings_base import *

# Force isolated in-memory SQLite for tests (deterministic + fast)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable migrations in TEST ONLY to bypass historical migration pollution
# This creates tables directly from model definitions without replaying migration history
class DisableMigrations(dict):
    """Django migration disabler for test environments."""
    
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Test-specific overrides
DEBUG = True
SECRET_KEY = 'test-secret-key-for-kernel-tests-only-not-for-production'

# Disable external services in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

