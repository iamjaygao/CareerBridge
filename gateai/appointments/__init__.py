"""
Backward compatibility shadow module for appointments app.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'decision_slots' instead of 'appointments'.

Example:
    Old: from appointments.models import Appointment
    New: from decision_slots.models import Appointment
"""

import warnings
import sys

# Emit deprecation warning on import
warnings.warn(
    "The 'appointments' app is deprecated. Use 'decision_slots' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from decision_slots to maintain backward compatibility
try:
    import decision_slots
    from decision_slots import *  # Re-export all modules
    
    # Register submodules in sys.modules for imports like 'from appointments.models import ...'
    sys.modules['appointments.models'] = decision_slots.models
    sys.modules['appointments.views'] = decision_slots.views
    sys.modules['appointments.serializers'] = decision_slots.serializers
    sys.modules['appointments.urls'] = decision_slots.urls
    sys.modules['appointments.admin'] = decision_slots.admin
    sys.modules['appointments.tasks'] = decision_slots.tasks
    
except ImportError as e:
    raise ImportError(
        f"The 'appointments' compatibility module requires 'decision_slots' to be available. "
        f"Please ensure the decision_slots app is installed. "
        f"Original error: {e}"
    )

__all__ = [
    'models',
    'views',
    'serializers',
    'urls',
    'admin',
    'tasks',
]

