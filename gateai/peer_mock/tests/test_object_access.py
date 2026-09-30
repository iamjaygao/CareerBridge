"""
IDOR tests for the PR1 peer mock API (design doc §8.2).

User A must never read or change user B's profile or registration. Every
endpoint acts on request.user; these tests point every client-controlled input
(query params, body fields) at B and assert B is untouched.
"""

from django.test import TestCase
from django.urls import URLResolver, get_resolver

from peer_mock.models import AvailabilityWindow, PeerEvent, PeerProfile, Registration

from .helpers import client_for, frozen, make_round, make_user, onboard, onboarding_body, power_peer_mock


def window(day, start, end):
    return {'date': day, 'start': start, 'end': end}


class PeerMockObjectAccessTest(TestCase):

    def setUp(self):
        power_peer_mock()
        self.a, self.b = make_user('alice'), make_user('bob')
        onboard(self.a, name='Alice')
        self.b_profile = onboard(self.b, tz='Europe/London', name='Bob')
        self.round = make_round()
        self.url = f'/api/v1/peer-mock/rounds/{self.round.public_id}/registration/'
        with frozen():
            client_for(self.b).put(self.url, {'interview_type': 'coding', 'direction': 'backend',
                                              'windows': [window('2026-11-03', '18:00', '20:00')]}, format='json')
        self.b_windows = self.windows_of(self.b)
        self.b_events = PeerEvent.objects.filter(user=self.b).count()
        self.client_a = client_for(self.a)

    @staticmethod
    def windows_of(user):
        return list(AvailabilityWindow.objects.filter(registration__user=user).values_list('start_utc', 'end_utc'))

    def assert_b_untouched(self):
        profile = PeerProfile.objects.get(user=self.b)
        self.assertEqual((profile.display_name, profile.timezone), ('Bob', 'Europe/London'))
        registration = Registration.objects.get(user=self.b)
        self.assertEqual((registration.status, registration.interview_type), ('active', 'coding'))
        self.assertEqual(self.windows_of(self.b), self.b_windows)
        self.assertEqual(PeerEvent.objects.filter(user=self.b).count(), self.b_events)

    def test_profile_is_always_the_callers(self):
        response = self.client_a.get('/api/v1/peer-mock/me/profile/', {'user_id': self.b.pk, 'user': self.b.pk})
        self.assertEqual(response.json()['display_name'], 'Alice')
        body = onboarding_body(display_name='Hacked', timezone='Asia/Tokyo', user=self.b.pk, user_id=self.b.pk)
        self.assertEqual(self.client_a.put('/api/v1/peer-mock/me/profile/', body, format='json').status_code, 200)
        self.assertEqual(PeerProfile.objects.get(user=self.a).display_name, 'Hacked')
        self.assert_b_untouched()

    def test_registration_of_another_user_is_not_readable(self):
        with frozen():
            response = self.client_a.get(self.url, {'user_id': self.b.pk, 'user': self.b.pk})
            current = self.client_a.get('/api/v1/peer-mock/rounds/current/', {'user_id': self.b.pk}).json()
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('2026-11-03', response.content.decode())
        self.assertIsNone(current['my_registration'])

    def test_writes_only_touch_the_callers_registration(self):
        body = {'interview_type': 'behavioral', 'direction': '', 'user': self.b.pk, 'user_id': self.b.pk,
                'windows': [window('2026-11-05', '09:00', '10:00')]}
        with frozen():
            self.assertEqual(self.client_a.put(self.url, body, format='json').status_code, 200)
            self.assertEqual(self.client_a.delete(self.url, {'user_id': self.b.pk}).status_code, 204)
            self.assertEqual(self.client_a.delete(f'{self.url}?user_id={self.b.pk}').status_code, 204)
        self.assertEqual(Registration.objects.get(user=self.a).status, 'withdrawn')
        self.assert_b_untouched()

    def test_no_peer_mock_route_takes_a_user_id(self):
        resolver = next(p for p in get_resolver().url_patterns
                        if isinstance(p, URLResolver) and str(p.pattern) == 'api/v1/peer-mock/')
        params = {name for p in resolver.url_patterns for name in p.pattern.converters}
        self.assertEqual(params, {'round_id'})
