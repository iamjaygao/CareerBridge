"""Kernel periodic tasks."""

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

HEARTBEAT_CACHE_KEY = 'kernel:beat:last_heartbeat'


@shared_task
def beat_heartbeat() -> str:
    """Record that beat -> broker -> worker delivered a task (checked by ops/CI)."""
    now = timezone.now().isoformat()
    cache.set(HEARTBEAT_CACHE_KEY, now, timeout=None)
    return now
