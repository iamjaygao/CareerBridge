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

# Periodic tasks are gated by the bus of the module their function belongs to.
GATED_TASKS = {
    'chat.tasks.notify_staff_unanswered_chats': 'CHAT_BUS',
    # Appointment/mentor notifications belong to the mentor module.
    'decision_slots.tasks.notify_staff_upcoming_appointments': 'MENTOR_BUS',
    'decision_slots.tasks.notify_staff_unconfirmed_appointments': 'MENTOR_BUS',
    'decision_slots.tasks.notify_staff_missing_mentor_feedback': 'MENTOR_BUS',
    'decision_slots.tasks.notify_admin_slot_conflicts': 'MENTOR_BUS',
    'adminpanel.tasks.notify_admin_payment_success_drop': 'PAYMENT_BUS',
    'adminpanel.tasks.notify_admin_metric_anomaly': 'ADMIN_BUS',
    'adminpanel.tasks.notify_admin_risk_alerts': 'ADMIN_BUS',
    # System alerts to superadmins always run (KERNEL_CORE_BUS cannot be switched off).
    'adminpanel.tasks.notify_superadmin_system_alerts': 'KERNEL_CORE_BUS',
}
ALWAYS_ON = {'KERNEL_CORE_BUS'}


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
            if bus in ALWAYS_ON:
                continue
            with self.subTest(task=dotted):
                self.set_bus(bus, 'OFF')
                self.assertEqual(load_task(dotted).run(*self.args_for(dotted)), 'skipped: bus off')

    def test_superadmin_alerts_run_with_every_other_bus_off(self):
        BusPowerState.objects.all().delete()
        BusPowerState.objects.bulk_create([BusPowerState(bus_name=n, state='ON' if n == 'KERNEL_CORE_BUS' else 'OFF')
                                           for n in BUS_POWER_DEFAULTS])
        invalidate_cache()
        task = load_task('adminpanel.tasks.notify_superadmin_system_alerts')
        self.assertNotEqual(task.run(), 'skipped: bus off')

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
            # Fake SMTP settings (required by settings_prod since M3; never used to send).
            'EMAIL_HOST': 'smtp.example.invalid',
            'EMAIL_PORT': '587',
            'EMAIL_HOST_USER': 'test',
            'EMAIL_HOST_PASSWORD': 'test-only-not-real',
            'EMAIL_USE_TLS': 'true',
            'DEFAULT_FROM_EMAIL': 'test@example.invalid',
        }
        code = ('import django; django.setup(); from django.conf import settings as s; '
                'print(s.CELERY_BROKER_URL); print(s.CACHES["default"]["BACKEND"])')
        out = subprocess.run([sys.executable, '-c', code], cwd=str(Path(settings.BASE_DIR)), env=env,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-1500:])
        broker, backend = out.stdout.split()
        self.assertEqual(broker, 'redis://redis:6379/3')
        self.assertEqual(backend, 'django.core.cache.backends.redis.RedisCache')
