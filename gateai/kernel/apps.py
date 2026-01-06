from django.apps import AppConfig


class KernelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kernel"

    def ready(self):
        # Import listeners registration side-effects
        try:
            import kernel.listeners  # noqa: F401
        except Exception:
            # Avoid hard failures during migrations; listeners will be registered once apps are ready
            pass

