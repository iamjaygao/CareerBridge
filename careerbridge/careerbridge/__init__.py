"""
Backward compatibility shadow module for careerbridge.careerbridge.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'gateai.gateai' instead of 'careerbridge.careerbridge'.
"""

import warnings
import sys

warnings.warn(
    "The 'careerbridge.careerbridge' package is deprecated. Use 'gateai.gateai' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from gateai.gateai
try:
    from gateai.gateai import *  # Re-export all submodules
    from gateai.gateai.celery import app as celery_app
    from gateai.gateai import settings, urls, wsgi, asgi
    
    # Make submodules accessible
    sys.modules['careerbridge.careerbridge.settings'] = gateai.gateai.settings
    sys.modules['careerbridge.careerbridge.urls'] = gateai.gateai.urls
    sys.modules['careerbridge.careerbridge.wsgi'] = gateai.gateai.wsgi
    sys.modules['careerbridge.careerbridge.asgi'] = gateai.gateai.asgi
    sys.modules['careerbridge.careerbridge.celery'] = gateai.gateai.celery
    
    # Celery compatibility
    app = celery_app
    celery = celery_app
except ImportError as e:
    raise ImportError(
        f"The 'careerbridge.careerbridge' compatibility module requires 'gateai.gateai' to be available. "
        f"Please ensure the gateai package is installed and accessible. "
        f"Original error: {e}"
    )

__all__ = [
    'settings',
    'urls',
    'wsgi',
    'asgi',
    'celery',
    'celery_app',
    'app',
]

