from django.apps import AppConfig


class KernelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kernel'
    verbose_name = 'Kernel'
    
    def ready(self):
        """Import governance models and admin when app is ready"""
        # Import governance models to ensure they're registered
        from kernel.governance import models as governance_models
        from kernel.governance import admin as governance_admin
