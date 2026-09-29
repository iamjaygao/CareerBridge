"""
/health/ is for load balancers and the Docker healthcheck:
- reachable anonymously under every bus / feature-flag combination;
- 200 only when the database and cache work, 503 otherwise.
"""

import itertools
from unittest import mock

from django.test import TestCase

from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

URL = '/health/'


def set_buses(states):
    BusPowerState.objects.all().delete()
    BusPowerState.objects.bulk_create([BusPowerState(bus_name=n, state=s) for n, s in states.items()])
    invalidate_cache()


class HealthReachabilityTest(TestCase):

    def setUp(self):
        self.addCleanup(invalidate_cache)

    def assert_healthy(self, label):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200, f'{label}: {response.content[:200]}')
        self.assertEqual(response.json()['status'], 'healthy', label)

    def test_under_default_buses(self):
        set_buses(BUS_POWER_DEFAULTS)
        self.assert_healthy('defaults')

    def test_under_every_single_bus_off_and_all_off(self):
        buses = [b for b in BUS_POWER_DEFAULTS if b != 'KERNEL_CORE_BUS']
        combos = [dict.fromkeys(buses, 'OFF'), dict.fromkeys(buses, 'ON')]
        combos += [{**dict.fromkeys(buses, 'ON'), b: 'OFF'} for b in buses]
        for combo in combos:
            with self.subTest(combo=combo):
                set_buses({**combo, 'KERNEL_CORE_BUS': 'ON'})
                self.assert_healthy(str(combo))

    def test_without_governance_and_with_every_flag_off(self):
        set_buses(BUS_POWER_DEFAULTS)
        self.assert_healthy('no PlatformState')
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[], reason='t')
        for key in ('USERS', 'KERNEL_ADMIN', 'PEER_MOCK', 'HEALTH'):
            FeatureFlag.objects.create(key=key, state='OFF', visibility='internal', reason='t')
        self.assert_healthy('all flags OFF')

    def test_is_anonymous(self):
        set_buses(dict.fromkeys(BUS_POWER_DEFAULTS, 'OFF') | {'KERNEL_CORE_BUS': 'ON'})
        self.assertEqual(self.client.get(URL).status_code, 200)


class HealthStatusCodeTest(TestCase):

    def setUp(self):
        set_buses(BUS_POWER_DEFAULTS)
        self.addCleanup(invalidate_cache)

    def test_database_failure_is_503(self):
        with mock.patch('gateai.views.connection.ensure_connection', side_effect=Exception('db down')):
            response = self.client.get(URL)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['components']['database'], 'unhealthy')

    def test_cache_failure_is_503(self):
        with mock.patch('gateai.views.cache.get', return_value=None):
            response = self.client.get(URL)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['components']['cache'], 'unhealthy')
