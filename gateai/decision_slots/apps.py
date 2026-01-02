from django.apps import AppConfig


class DecisionSlotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'decision_slots'
    label = 'decision_slots'  # Explicit label to match name
