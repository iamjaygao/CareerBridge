from django.apps import AppConfig


class HumanLoopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'human_loop'
    label = 'human_loop'  # Explicit label to match name
