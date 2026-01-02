
from .celery import app as celery_app

# Celery looks for `app` or `celery` on the module when using `-A gateai`.
app = celery_app
celery = celery_app

__all__ = ("celery_app", "app", "celery")
