from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


def check_settings():
    """The ops timezone must be a valid IANA name; fail at startup, not at the first round."""
    from django.conf import settings

    from .timeutil import LocalTimeError, get_zone

    try:
        get_zone(settings.PEER_MOCK_OPS_TZ)
    except LocalTimeError as exc:
        raise ImproperlyConfigured(f'PEER_MOCK_OPS_TZ: {exc.message}') from exc


class PeerMockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'peer_mock'

    def ready(self):
        check_settings()
        from . import signals  # noqa: F401  (registers receivers)
