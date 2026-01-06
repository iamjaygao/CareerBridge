from django.apps import AppConfig


# Module-level guard to prevent duplicate registrations
_CALLBACK_REGISTERED = False


class DecisionSlotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'decision_slots'
    label = 'decision_slots'  # Explicit label to match name
    
    def ready(self):
        """Register kernel callbacks on app initialization."""
        global _CALLBACK_REGISTERED
        
        if _CALLBACK_REGISTERED:
            return  # Idempotent guard
        
        # Import here to avoid circular dependency
        from gateai.kernel_events import register_resource_release_callback
        from decision_slots.kernel_callbacks import release_locks_for_failure
        
        # Register decision_slots callback with kernel
        register_resource_release_callback(release_locks_for_failure)
        
        _CALLBACK_REGISTERED = True
