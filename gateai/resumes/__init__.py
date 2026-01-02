"""
Backward compatibility shadow module for resumes app.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'ats_signals' instead of 'resumes'.

Example:
    Old: from resumes.models import Resume
    New: from ats_signals.models import Resume
"""

import warnings
import sys

# Emit deprecation warning on import
warnings.warn(
    "The 'resumes' app is deprecated. Use 'ats_signals' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from ats_signals to maintain backward compatibility
try:
    import ats_signals
    from ats_signals import *  # Re-export all modules
    
    # Register submodules in sys.modules for imports like 'from resumes.models import ...'
    sys.modules['resumes.models'] = ats_signals.models
    sys.modules['resumes.views'] = ats_signals.views
    sys.modules['resumes.serializers'] = ats_signals.serializers
    sys.modules['resumes.services'] = ats_signals.services
    sys.modules['resumes.urls'] = ats_signals.urls
    sys.modules['resumes.admin'] = ats_signals.admin
    sys.modules['resumes.external_services'] = ats_signals.external_services
    sys.modules['resumes.legal_disclaimers'] = ats_signals.legal_disclaimers
    sys.modules['resumes.data_management'] = ats_signals.data_management
    sys.modules['resumes.referral_service'] = ats_signals.referral_service
    sys.modules['resumes.tier_service'] = ats_signals.tier_service
    
except ImportError as e:
    raise ImportError(
        f"The 'resumes' compatibility module requires 'ats_signals' to be available. "
        f"Please ensure the ats_signals app is installed. "
        f"Original error: {e}"
    )

__all__ = [
    'models',
    'views',
    'serializers',
    'services',
    'urls',
    'admin',
]

