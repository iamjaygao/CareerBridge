"""
Development Django settings for careerbridge project.

This file contains settings specific to the development environment.
"""

from .settings_base import *

# Ensure local .env values override any shell defaults in development.
load_dotenv(BASE_DIR / '.env', override=True)
CELERY_BROKER_URL = os.environ.get('REDIS_URL', CELERY_BROKER_URL)
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', CELERY_RESULT_BACKEND)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-k@p%&#5aru7wivstcjgrnd1fhlm=qvvn-e5apz$o^h-ux-4nxw')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'testserver',
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'careerbridge'),
        'USER': os.environ.get('POSTGRES_USER', 'careerbridge_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'careerbridge_dev_pwd'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development-specific settings
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Payment Configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_stripe_secret_key')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_your_stripe_publishable_key')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_stripe_webhook_secret')

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'your_paypal_client_id')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', 'your_paypal_client_secret')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # or 'live'

# Add payments app to INSTALLED_APPS
INSTALLED_APPS += ['payments'] 
