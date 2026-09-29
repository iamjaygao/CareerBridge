from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
import json

from human_loop.models import MentorProfile
from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache
from django.contrib.auth import get_user_model


def seed_payment_bus(state):
    BusPowerState.objects.all().delete()
    BusPowerState.objects.bulk_create([
        BusPowerState(bus_name=n, state=v)
        for n, v in {**BUS_POWER_DEFAULTS, 'PAYMENT_BUS': state}.items()
    ])
    invalidate_cache()


class StripeWebhookTests(TestCase):
    def setUp(self):
        # PAYMENT_BUS on and governance initialised, so the webhook view runs.
        seed_payment_bus('ON')
        self.addCleanup(invalidate_cache)
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[], reason='t')
        FeatureFlag.objects.create(key='PAYMENTS', state='ON', visibility='public', reason='t')

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    @patch('stripe.Webhook.construct_event')
    def test_webhook_is_404_when_payment_bus_is_off(self, mock_construct_event):
        """Control: with PAYMENT_BUS off the webhook is hidden and never runs."""
        seed_payment_bus('OFF')
        url = reverse('payments:stripe_webhook')
        resp = self.client.post(url, data='{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='t')
        self.assertEqual(resp.status_code, 404)
        mock_construct_event.assert_not_called()

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    @patch('stripe.Webhook.construct_event')
    def test_account_updated_updates_mentor_fields(self, mock_construct_event):
        User = get_user_model()
        user = User.objects.create_user(username='mentor1', email='m1@example.com', password='pass')
        mentor = MentorProfile.objects.create(user=user, bio='bio')

        event = {
            'type': 'account.updated',
            'id': 'evt_test',
            'data': {
                'object': {
                    'id': 'acct_123',
                    'payouts_enabled': True,
                    'charges_enabled': False,
                    'requirements': {
                        'disabled_reason': 'requirements.past_due',
                        'current_deadline': int(timezone.now().timestamp())
                    },
                    'capabilities': {'transfers': 'active'}
                }
            }
        }
        mentor.stripe_account_id = 'acct_123'
        mentor.save()

        mock_construct_event.return_value = event

        payload = json.dumps({'dummy': 'payload'})
        url = reverse('payments:stripe_webhook')
        resp = self.client.post(url, data=payload, content_type='application/json', HTTP_STRIPE_SIGNATURE='t')
        self.assertEqual(resp.status_code, 200)

        mentor.refresh_from_db()
        self.assertTrue(mentor.payouts_enabled)
        self.assertFalse(mentor.charges_enabled)
        self.assertEqual(mentor.kyc_disabled_reason, 'requirements.past_due')
        self.assertIn('transfers', mentor.stripe_capabilities)

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    @patch('stripe.Webhook.construct_event')
    def test_duplicate_event_is_idempotent(self, mock_construct_event):
        event = {'type': 'payment_intent.succeeded', 'id': 'evt_dup', 'data': {'object': {'id': 'pi_1'}}}
        mock_construct_event.return_value = event
        payload = json.dumps({'dummy': 'payload'})
        url = reverse('payments:stripe_webhook')
        r1 = self.client.post(url, data=payload, content_type='application/json', HTTP_STRIPE_SIGNATURE='t')
        r2 = self.client.post(url, data=payload, content_type='application/json', HTTP_STRIPE_SIGNATURE='t')
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
from django.test import TestCase

# Create your tests here.
