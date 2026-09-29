"""
Celery beat: a heartbeat proves the scheduler -> broker -> worker path, and
periodic tasks of unlaunched modules do nothing while their bus is OFF.
"""

import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from kernel.governance.models import BusPowerState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

# Periodic tasks of modules that are not launched, and the bus that gates each.
GATED_TASKS = {
    'chat.tasks.notify_staff_unanswered_chats': 'AI_BUS',
    'decision_slots.tasks.notify_staff_upcoming_appointments': 'AI_BUS',
    'decision_slots.tasks.notify_staff_unconfirmed_appointments': 'AI_BUS',
    'decision_slots.tasks.notify_staff_missing_mentor_feedback': 'AI_BUS',
    'decision_slots.tasks.notify_admin_slot_conflicts': 'AI_BUS',
    'adminpanel.tasks.notify_admin_payment_success_drop': 'PAYMENT_BUS',
    'adminpanel.tasks.notify_admin_metric_anomaly': 'ADMIN_BUS',
    'adminpanel.tasks.notify_admin_risk_alerts': 'ADMIN_BUS',
    'adminpanel.tasks.notify_superadmin_system_alerts': 'ADMIN_BUS',
}


def load_task(dotted):
    module, name = dotted.rsplit('.', 1)
    return getattr(__import__(module, fromlist=[name]), name)


class HeartbeatTest(TestCase):

    def test_heartbeat_is_scheduled(self):
        entries = {e['task'] for e in settings.CELERY_BEAT_SCHEDULE.values()}
        self.assertIn('kernel.tasks.beat_heartbeat', entries)

    def test_heartbeat_records_a_timestamp(self):
        from kernel.tasks import beat_heartbeat, HEARTBEAT_CACHE_KEY
        cache.delete(HEARTBEAT_CACHE_KEY)
        beat_heartbeat()
        self.assertIsNotNone(cache.get(HEARTBEAT_CACHE_KEY))


class BusGatedTasksTest(TestCase):

    def setUp(self):
        self.addCleanup(invalidate_cache)

    def set_bus(self, bus, state):
        BusPowerState.objects.all().delete()
        BusPowerState.objects.bulk_create(
            [BusPowerState(bus_name=n, state=s) for n, s in {**BUS_POWER_DEFAULTS, bus: state}.items()])
        invalidate_cache()

    def test_every_scheduled_task_is_gated_or_kernel(self):
        for entry in settings.CELERY_BEAT_SCHEDULE.values():
            task = entry['task']
            with self.subTest(task=task):
                if task.startswith('kernel.'):
                    continue
                self.assertEqual(GATED_TASKS.get(task), getattr(load_task(task), 'required_bus', None))

    def test_gated_task_does_nothing_while_its_bus_is_off(self):
        for dotted, bus in GATED_TASKS.items():
            with self.subTest(task=dotted):
                self.set_bus(bus, 'OFF')
                self.assertEqual(load_task(dotted).run(*self.args_for(dotted)), 'skipped: bus off')

    @staticmethod
    def args_for(dotted):
        for entry in settings.CELERY_BEAT_SCHEDULE.values():
            if entry['task'] == dotted:
                return entry.get('args', ())
        return ()


class BrokerSettingsTest(SimpleTestCase):

    def test_prod_uses_celery_broker_url_and_redis_cache(self):
        env = {
            'PATH': '/usr/bin:/bin', 'DJANGO_SETTINGS_MODULE': 'gateai.settings_prod',
            'SECRET_KEY': 'x', 'ALLOWED_HOSTS': 'h', 'CORS_ALLOWED_ORIGINS': 'https://h',
            'CSRF_TRUSTED_ORIGINS': 'https://h', 'DATABASE_URL': 'postgresql://a:b@db:5432/app',
            'REDIS_URL': 'redis://redis:6379/0', 'CELERY_BROKER_URL': 'redis://redis:6379/3',
        }
        code = ('import django; django.setup(); from django.conf import settings as s; '
                'print(s.CELERY_BROKER_URL); print(s.CACHES["default"]["BACKEND"])')
        out = subprocess.run([sys.executable, '-c', code], cwd=str(Path(settings.BASE_DIR)), env=env,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-1500:])
        broker, backend = out.stdout.split()
        self.assertEqual(broker, 'redis://redis:6379/3')
        self.assertEqual(backend, 'django.core.cache.backends.redis.RedisCache')
