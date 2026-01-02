"""
Backward compatibility shadow module for notifications app.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'signal_delivery' instead of 'notifications'.

Example:
    Old: from notifications.models import Notification
    New: from signal_delivery.models import Notification
"""

import warnings
import sys

# Emit deprecation warning on import
warnings.warn(
    "The 'notifications' app is deprecated. Use 'signal_delivery' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from signal_delivery to maintain backward compatibility
try:
    import signal_delivery
    from signal_delivery import *  # Re-export all modules
    
    # Register submodules in sys.modules for imports like 'from notifications.models import ...'
    sys.modules['notifications.models'] = signal_delivery.models
    sys.modules['notifications.views'] = signal_delivery.views
    sys.modules['notifications.serializers'] = signal_delivery.serializers
    sys.modules['notifications.services'] = signal_delivery.services
    sys.modules['notifications.urls'] = signal_delivery.urls
    sys.modules['notifications.admin'] = signal_delivery.admin
    sys.modules['notifications.tasks'] = signal_delivery.tasks
    sys.modules['notifications.services.dispatcher'] = signal_delivery.services.dispatcher
    sys.modules['notifications.services.rules'] = signal_delivery.services.rules
    
except ImportError as e:
    raise ImportError(
        f"The 'notifications' compatibility module requires 'signal_delivery' to be available. "
        f"Please ensure the signal_delivery app is installed. "
        f"Original error: {e}"
    )

__all__ = [
    'models',
    'views',
    'serializers',
    'services',
    'urls',
    'admin',
    'tasks',
]

