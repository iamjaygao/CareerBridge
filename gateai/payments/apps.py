from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        # Register kernel listeners for payment execution boundary
        from payments.kernel_listeners import register_listeners  # noqa: WPS433

        register_listeners()
