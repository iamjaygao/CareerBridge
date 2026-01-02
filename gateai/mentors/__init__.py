"""
Backward compatibility shadow module for mentors app.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please update your imports to use 'human_loop' instead of 'mentors'.

Example:
    Old: from mentors.models import MentorProfile
    New: from human_loop.models import MentorProfile
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "The 'mentors' app is deprecated. Use 'human_loop' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Lazy import pattern - only import when actually accessed
# This prevents issues during migrations when modules may not be fully initialized
def _lazy_import():
    """Lazy import of human_loop modules."""
    import sys
    try:
        import human_loop
        # Only register if human_loop is fully loaded and has required attributes
        # Check for views specifically since that's what was causing the error
        if hasattr(human_loop, 'models') and hasattr(human_loop, 'views'):
            try:
                # Register submodules in sys.modules for imports like 'from mentors.models import ...'
                # Only register if the attribute actually exists
                if hasattr(human_loop, 'models'):
                    sys.modules['mentors.models'] = human_loop.models
                if hasattr(human_loop, 'views'):
                    sys.modules['mentors.views'] = human_loop.views
                if hasattr(human_loop, 'serializers'):
                    sys.modules['mentors.serializers'] = human_loop.serializers
                if hasattr(human_loop, 'services'):
                    sys.modules['mentors.services'] = human_loop.services
                if hasattr(human_loop, 'urls'):
                    sys.modules['mentors.urls'] = human_loop.urls
                if hasattr(human_loop, 'admin'):
                    sys.modules['mentors.admin'] = human_loop.admin
                if hasattr(human_loop, 'tasks'):
                    sys.modules['mentors.tasks'] = human_loop.tasks
                if hasattr(human_loop, 'dto'):
                    sys.modules['mentors.dto'] = human_loop.dto
            except (AttributeError, TypeError):
                # If any attribute access fails, skip sys.modules registration
                # This can happen during migrations when modules aren't fully initialized
                pass
        return human_loop
    except (ImportError, AttributeError, TypeError) as e:
        # During migrations, it's OK if some modules aren't available
        # Just return None and let the actual import fail later if needed
        return None

# Store lazy import function
_lazy_human_loop = None

def __getattr__(name):
    """Lazy attribute access for backward compatibility."""
    global _lazy_human_loop
    if _lazy_human_loop is None:
        _lazy_human_loop = _lazy_import()
    
    if _lazy_human_loop is None:
        raise AttributeError(f"module 'mentors' has no attribute '{name}'. "
                           f"Please use 'human_loop.{name}' instead.")
    
    return getattr(_lazy_human_loop, name)

__all__ = [
    'models',
    'views',
    'serializers',
    'services',
    'urls',
    'admin',
    'tasks',
    'dto',
]

