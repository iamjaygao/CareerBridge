"""
Production Django settings for careerbridge project.
"""

import os
from urllib.parse import urlparse

from .settings_base import *

DEBUG = False

def _require_env(name: str) -> str:
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('Missing required environment variable: DJANGO_SECRET_KEY or SECRET_KEY')

allowed_hosts_env = _require_env('ALLOWED_HOSTS')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url:
    parsed = urlparse(database_url)
    if not parsed.password:
        raise RuntimeError('DATABASE_URL has no password (is POSTGRES_PASSWORD set?)')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username or '',
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname or '',
            'PORT': parsed.port or '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _require_env('POSTGRES_DB'),
            'USER': _require_env('POSTGRES_USER'),
            'PASSWORD': _require_env('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True') == 'True'

cors_origins_env = _require_env('CORS_ALLOWED_ORIGINS')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]

csrf_trusted_env = _require_env('CSRF_TRUSTED_ORIGINS')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_trusted_env.split(',') if origin.strip()]

# Shared cache across all processes/containers (health check, beat heartbeat,
# throttling). Without this each process had its own in-memory cache.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        # Not a secret; same default host as the Celery broker in settings_base.
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    }
}
