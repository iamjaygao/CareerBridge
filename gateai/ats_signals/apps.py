from django.apps import AppConfig


class ATSSignalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ats_signals'
    label = 'ats_signals'  # Explicit label to match name
