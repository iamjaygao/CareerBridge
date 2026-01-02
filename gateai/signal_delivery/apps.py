from django.apps import AppConfig


class SignalDeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'signal_delivery'
    label = 'signal_delivery'  # Explicit label to match name
