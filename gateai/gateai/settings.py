"""
Django settings for gateai project.

Selects settings from the DJANGO_ENV environment variable, which is required:
- development, test -> settings_dev
- production        -> settings_prod

There is no default. An unset or unknown value is an error, so a server that
forgot DJANGO_ENV can never silently run with the development settings.

Setting DJANGO_SETTINGS_MODULE to a specific module (as the Docker image does
with gateai.settings_prod) bypasses this file entirely.
"""

import os

_DEV_ENVS = ('development', 'test')
_PROD_ENVS = ('production',)

environment = os.environ.get('DJANGO_ENV')

if environment in _PROD_ENVS:
    from .settings_prod import *
elif environment in _DEV_ENVS:
    from .settings_dev import *
else:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        f"DJANGO_ENV must be one of {', '.join(_DEV_ENVS + _PROD_ENVS)} "
        f"(got {environment!r}). Set it explicitly; there is no default."
    )
