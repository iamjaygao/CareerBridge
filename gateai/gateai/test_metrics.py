"""
/metrics/ serves Prometheus metrics to the scraper only.

- Disabled (404) unless METRICS_TOKEN is configured.
- Requires `Authorization: Bearer <METRICS_TOKEN>` (401 without, 403 if wrong).
- Not affected by bus power (monitoring must work while modules are OFF).
"""

from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve

from kernel.governance.models import BusPowerState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

URL = '/metrics/'
TOKEN = 'test-metrics-token'


class MetricsEndpointTest(TestCase):

    def setUp(self):
        BusPowerState.objects.bulk_create(
            [BusPowerState(bus_name=n, state=('ON' if n == 'KERNEL_CORE_BUS' else 'OFF')) for n in BUS_POWER_DEFAULTS])
        invalidate_cache()
        self.addCleanup(invalidate_cache)

    @override_settings(METRICS_TOKEN='')
    def test_disabled_without_configured_token(self):
        self.assertEqual(self.client.get(URL, HTTP_AUTHORIZATION=f'Bearer {TOKEN}').status_code, 404)

    @override_settings(METRICS_TOKEN=TOKEN)
    def test_requires_bearer_token(self):
        self.assertEqual(self.client.get(URL).status_code, 401)
        self.assertEqual(self.client.get(URL, HTTP_AUTHORIZATION='Bearer wrong').status_code, 403)

    @override_settings(METRICS_TOKEN=TOKEN)
    def test_serves_prometheus_metrics_with_all_buses_off(self):
        self.client.get('/health/')  # generate at least one observed request
        response = self.client.get(URL, HTTP_AUTHORIZATION=f'Bearer {TOKEN}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/plain'))
        body = response.content.decode()
        self.assertIn('django_http_requests_total_by_method_total', body)
        self.assertIn('django_http_requests_latency_seconds_by_view_method', body)

    def test_old_broken_metrics_route_is_gone(self):
        with self.assertRaises(Resolver404):
            resolve('/api/v1/services/metrics/')
