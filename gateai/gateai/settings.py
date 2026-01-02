"""
Django settings for gateai project.

This file imports the appropriate settings based on the environment.
For development, it imports from settings_dev.py
For production, it imports from settings_prod.py

To switch environments, set the DJANGO_SETTINGS_MODULE environment variable:
- Development: export DJANGO_SETTINGS_MODULE=gateai.settings_dev
- Production: export DJANGO_SETTINGS_MODULE=gateai.settings_prod
"""

import os

# Determine which settings to use based on environment
environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .settings_prod import *
else:
    from .settings_dev import *