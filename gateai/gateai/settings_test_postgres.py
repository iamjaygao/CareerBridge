"""
Test settings that run the suite against a real PostgreSQL server.

Identical to what `manage.py test` gets from settings_dev, except that the
database is Postgres instead of the SQLite file that settings_dev forces when
'test' is on the command line. Migrations are applied as normal, so the full
migration history is replayed against Postgres.

All connection values come from the environment and there are no defaults:
a missing variable fails loudly instead of falling back to a built-in password.

Used by the `backend-postgres` CI job. MUST NOT be used outside tests.
"""

from .settings_dev import *  # noqa: F401,F403


def _require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be set to run tests against Postgres")
    return value


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _require_env('POSTGRES_DB'),
        'USER': _require_env('POSTGRES_USER'),
        'PASSWORD': _require_env('POSTGRES_PASSWORD'),
        'HOST': _require_env('POSTGRES_HOST'),
        'PORT': _require_env('POSTGRES_PORT'),
    }
}
