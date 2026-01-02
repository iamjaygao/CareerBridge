"""
Backward compatibility shadow module for careerbridge.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'gateai' instead of 'careerbridge'.

Example:
    Old: from careerbridge.settings import *
    New: from gateai.settings import *
"""

import warnings
import sys

# Emit deprecation warning on import
warnings.warn(
    "The 'careerbridge' package is deprecated. Use 'gateai' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from gateai to maintain backward compatibility
try:
    # Import gateai modules and make them available as careerbridge.*
    import gateai
    import gateai.gateai as careerbridge_module
    
    # Make submodules accessible via careerbridge.*
    sys.modules['careerbridge.settings'] = gateai.gateai.settings
    sys.modules['careerbridge.urls'] = gateai.gateai.urls
    sys.modules['careerbridge.wsgi'] = gateai.gateai.wsgi
    sys.modules['careerbridge.asgi'] = gateai.gateai.asgi
    sys.modules['careerbridge.celery'] = gateai.gateai.celery
    sys.modules['careerbridge.careerbridge'] = gateai.gateai
    
except ImportError as e:
    # If gateai is not available, this is a problem
    raise ImportError(
        f"The 'careerbridge' compatibility module requires 'gateai' to be available. "
        f"Please ensure the gateai package is installed and accessible. "
        f"Original error: {e}"
    )

__all__ = [
    'settings',
    'urls',
    'wsgi',
    'asgi',
    'celery',
]

