"""
Current round and registration with availability windows (design doc §2.3).

Times are frozen at NOW (Tue 2026-10-20 12:00Z); the round of week 2026-11-01
is open, and its week contains the US fall-back change.
"""

from datetime import timedelta

from django.test import TestCase

from peer_mock.models import AvailabilityWindow, PeerEvent, Registration

from .helpers import NOW, client_for, frozen, make_round, make_user, onboard, power_peer_mock, utc


def window(day, start, end):
    return {'date': day, 'start': start, 'end': end}


class RegistrationTest(TestCase):

    def setUp(self):
        power_peer_mock()
        self.user = make_user('alex')
        self.profile = onboard(self.user)
        self.client = client_for(self.user)
        self.round = make_round()
        self.url = f'/api/v1/peer-mock/rounds/{self.round.public_id}/registration/'

    def put(self, windows, interview_type='coding', direction='backend', now=NOW):
        with frozen(now):
            return self.client.put(self.url, {'interview_type': interview_type, 'direction': direction,
                                              'windows': windows}, format='json')

    def windows_utc(self):
        return list(AvailabilityWindow.objects.filter(registration__user=self.user)
                    .values_list('start_utc', 'end_utc'))

    def test_submit_converts_echoes_and_logs(self):
        response = self.put([window('2026-11-03', '18:00', '20:00')])
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body['windows'][0]['local'], '2026-11-03 18:00–20:00 EST')
        self.assertEqual(body['windows'][0]['start_utc'], '2026-11-03T23:00:00Z')
        self.assertEqual(body['warnings'], [])
        self.assertEqual(self.windows_utc(), [(utc(2026, 11, 3, 23), utc(2026, 11, 4, 1))])
        event = PeerEvent.objects.get(event_type='availability_submitted')
        self.assertEqual((event.user, event.round_id, event.actor_ref), (self.user, self.round.id,
                                                                         self.profile.actor_ref))
        self.assertEqual(event.metadata, {'interview_type': 'coding', 'windows': 1, 'total_minutes': 120})

    def test_resubmitting_replaces_all_windows(self):
        self.put([window('2026-11-03', '18:00', '20:00'), window('2026-11-04', '18:00', '20:00')])
        self.put([window('2026-11-05', '09:00', '10:00')], interview_type='behavioral', direction='')
        self.assertEqual(self.windows_utc(), [(utc(2026, 11, 5, 14), utc(2026, 11, 5, 15))])
        registration = Registration.objects.get(user=self.user)
        self.assertEqual((registration.interview_type, registration.direction), ('behavioral', ''))
        self.assertEqual(Registration.objects.count(), 1)

    def test_errors_reject_the_whole_submission(self):
        self.put([window('2026-11-03', '18:00', '20:00')])
        response = self.put([window('2026-11-04', '18:00', '20:00'), window('2027-03-14', '02:30', '04:00')])
        self.assertEqual(response.status_code, 400)
        self.assertEqual([(e['window'], e['code']) for e in response.json()['windows']],
                         [(1, 'nonexistent_local_time')])
        self.assertEqual(self.windows_utc(), [(utc(2026, 11, 3, 23), utc(2026, 11, 4, 1))])  # unchanged

    def test_ambiguous_and_clipped_windows_are_echoed(self):
        # Earliest session start is Sun Nov 1 08:00 EST (Fri 09:00 EDT + 48h).
        response = self.put([window('2026-11-01', '01:30', '10:00')])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([w['code'] for w in response.json()['warnings']], ['ambiguous_local_time', 'clipped'])
        self.assertEqual(self.windows_utc(), [(self.round.earliest_session_start, utc(2026, 11, 1, 15))])

    def test_window_errors(self):
        cases = {
            'outside_round': [window('2026-11-09', '18:00', '20:00')],
            'window_too_short': [window('2026-11-03', '18:00', '18:45')],
            'invalid_time': [window('2026-11-03', '18:10', '20:00')],
            'too_many_windows': [window('2026-11-03', '18:00', '20:00')] * 21,
        }
        for code, windows in cases.items():
            with self.subTest(code=code):
                response = self.put(windows)
                self.assertEqual(response.status_code, 400)
                self.assertEqual([e['code'] for e in response.json()['windows']], [code])
        self.assertFalse(Registration.objects.exists())

    def test_direction_must_belong_to_the_type(self):
        response = self.put([window('2026-11-03', '18:00', '20:00')], interview_type='behavioral',
                            direction='backend')
        self.assertEqual(response.status_code, 400)
        self.assertIn('direction', response.json())

    def test_closed_round_rejects_changes(self):
        self.put([window('2026-11-03', '18:00', '20:00')])
        after_deadline = self.round.submission_deadline
        response = self.put([window('2026-11-04', '18:00', '20:00')], now=after_deadline)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['code'], 'round_closed')
        with frozen(after_deadline):
            self.assertEqual(self.client.delete(self.url).status_code, 409)
        type(self.round).objects.filter(pk=self.round.pk).update(status='matching')
        self.assertEqual(self.put([window('2026-11-04', '18:00', '20:00')]).status_code, 409)
        self.assertEqual(len(self.windows_utc()), 1)

    def test_withdraw_and_rejoin(self):
        with frozen():
            self.assertEqual(self.client.delete(self.url).status_code, 404)  # nothing to withdraw
        self.put([window('2026-11-03', '18:00', '20:00')])
        with frozen():
            self.assertEqual(self.client.delete(self.url).status_code, 204)
            self.assertEqual(self.client.delete(self.url).status_code, 204)  # idempotent
        registration = Registration.objects.get(user=self.user)
        self.assertEqual(registration.status, 'withdrawn')
        self.assertEqual(self.windows_utc(), [])
        self.assertEqual(PeerEvent.objects.filter(event_type='registration_withdrawn').count(), 1)
        self.put([window('2026-11-04', '18:00', '20:00')])
        self.assertEqual(Registration.objects.get(user=self.user).status, 'active')

    def test_unknown_round_is_404(self):
        with frozen():
            response = self.client.get('/api/v1/peer-mock/rounds/00000000-0000-0000-0000-000000000000/registration/')
        self.assertEqual(response.status_code, 404)

    def test_t24_changing_timezone_keeps_the_utc_windows(self):
        self.put([window('2026-11-03', '18:00', '20:00')])
        before = self.windows_utc()
        self.profile.timezone = 'Europe/London'
        self.profile.save()
        with frozen():
            body = self.client.get(self.url).json()
        self.assertEqual(self.windows_utc(), before)
        self.assertEqual(body['windows'][0]['local'], '2026-11-03 23:00 GMT – 2026-11-04 01:00 GMT')
        self.assertEqual(body['windows'][0]['submitted'],
                         {'local_start': '2026-11-03T18:00', 'local_end': '2026-11-03T20:00',
                          'tz': 'America/New_York'})


class CurrentRoundTest(TestCase):

    def setUp(self):
        power_peer_mock()
        self.user = make_user('alex')
        onboard(self.user, tz='Europe/London')
        self.client = client_for(self.user)

    def get(self, now=NOW):
        with frozen(now):
            return self.client.get('/api/v1/peer-mock/rounds/current/')

    def test_no_open_round(self):
        response = self.get()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 'no_open_round')

    def test_times_are_shown_in_the_users_timezone(self):
        rnd = make_round()
        body = self.get().json()
        self.assertEqual(body['id'], str(rnd.public_id))
        # Thu Oct 29 23:59 EDT is Fri 03:59 in London (GMT since Oct 25).
        self.assertEqual(body['submission_deadline'], '2026-10-30T03:59:00Z')
        self.assertEqual(body['submission_deadline_local'], 'Fri Oct 30, 03:59 GMT')
        self.assertIsNone(body['my_registration'])

    def test_after_the_deadline_the_next_round_is_current(self):
        first = make_round()
        second = make_round(first.week_key + timedelta(days=7))
        self.assertEqual(self.get(first.submission_deadline).json()['id'], str(second.public_id))
