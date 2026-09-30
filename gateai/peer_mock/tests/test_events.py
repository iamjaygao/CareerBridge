"""Event log writes (design doc §6.1)."""

from django.db import transaction
from django.test import TestCase

from peer_mock.events import emit
from peer_mock.models import PeerEvent

from .helpers import make_user


class UserEventsTest(TestCase):

    def test_signup_is_recorded_once(self):
        user = make_user('alex', verified=False)
        user.first_name = 'Alex'
        user.save()
        self.assertEqual(list(PeerEvent.objects.filter(user=user).values_list('event_type', flat=True)),
                         ['signup'])

    def test_email_verification_is_recorded_on_the_transition_only(self):
        user = make_user('alex', verified=False)
        user.email_verified = True
        user.save()
        user.save()
        reloaded = type(user).objects.get(pk=user.pk)
        reloaded.save()
        self.assertEqual(PeerEvent.objects.filter(user=user, event_type='email_verified').count(), 1)

    def test_already_verified_signup_records_no_verification_event(self):
        user = make_user('alex', verified=True)
        user.save()
        self.assertFalse(PeerEvent.objects.filter(user=user, event_type='email_verified').exists())


class EmitTest(TestCase):

    def test_duplicate_idempotency_key_is_ignored_without_breaking_the_transaction(self):
        with transaction.atomic():
            self.assertIsNotNone(emit('round_opened', actor_kind='system', idempotency_key='k1'))
            self.assertIsNone(emit('round_opened', actor_kind='system', idempotency_key='k1'))
            emit('round_opened', actor_kind='system', idempotency_key='k2')  # still usable
        self.assertEqual(PeerEvent.objects.filter(event_type='round_opened').count(), 2)
