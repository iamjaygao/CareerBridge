"""
The Stripe webhook is unauthenticated by design; the signature is its auth.
Forged or unsigned requests must be rejected before anything is stored.
"""

import hashlib
import hmac
import json
import time

from django.test import TestCase, override_settings

from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache
from payments.models import PaymentWebhook

URL = '/api/v1/payments/webhooks/stripe/'
SECRET = 'whsec_test_only_not_real'


def stripe_signature(payload: bytes, secret: str, timestamp: int) -> str:
    signed = f'{timestamp}.'.encode() + payload
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f't={timestamp},v1={digest}'


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
class StripeWebhookSignatureTest(TestCase):

    def setUp(self):
        BusPowerState.objects.all().delete()
        BusPowerState.objects.bulk_create([
            BusPowerState(bus_name=n, state=s)
            for n, s in {**BUS_POWER_DEFAULTS, 'PAYMENT_BUS': 'ON'}.items()
        ])
        invalidate_cache()
        self.addCleanup(invalidate_cache)
        # Governance initialised with PAYMENTS on (without it the middleware fails closed).
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[], reason='t')
        FeatureFlag.objects.create(key='PAYMENTS', state='ON', visibility='public', reason='t')
        self.payload = json.dumps({
            'id': 'evt_test_1', 'object': 'event', 'type': 'charge.refunded',
            'data': {'object': {'id': 'ch_test'}},
        }).encode()

    def post(self, signature=None):
        headers = {'HTTP_STRIPE_SIGNATURE': signature} if signature is not None else {}
        return self.client.post(URL, data=self.payload, content_type='application/json', **headers)

    def test_forged_signature_rejected(self):
        forged = stripe_signature(self.payload, 'whsec_attacker_guess', int(time.time()))
        response = self.post(forged)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PaymentWebhook.objects.exists())

    def test_missing_signature_rejected(self):
        response = self.post()
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PaymentWebhook.objects.exists())

    def test_stale_timestamp_rejected(self):
        old = stripe_signature(self.payload, SECRET, int(time.time()) - 3600)
        response = self.post(old)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PaymentWebhook.objects.exists())

    def test_correctly_signed_event_accepted(self):
        # Control case: proves the rejections above are about the signature.
        response = self.post(stripe_signature(self.payload, SECRET, int(time.time())))
        self.assertEqual(response.status_code, 200, response.content[:200])
        self.assertTrue(PaymentWebhook.objects.filter(event_id='evt_test_1').exists())
