"""
Round schedule (design doc §5.1, T25) and the ensure_rounds task.

Schedule points are wall times in PEER_MOCK_OPS_TZ, so they keep their local
time across DST changes; consecutive session windows touch and never overlap.
"""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings

from peer_mock.apps import check_settings
from peer_mock.models import PeerEvent, Round
from peer_mock.rounds import current_round, ensure_rounds, round_times, upcoming_week_keys
from peer_mock.tasks import ensure_rounds as ensure_rounds_task

from .helpers import make_round, power_peer_mock, utc

NY = ZoneInfo('America/New_York')


def local(dt, tz=NY):
    return dt.astimezone(tz).strftime('%a %H:%M')


class RoundScheduleTest(SimpleTestCase):

    def test_schedule_points_are_local_wall_times(self):
        t = round_times(date(2026, 10, 4))
        self.assertEqual(local(t['invite_at']), 'Mon 10:00')
        self.assertEqual(local(t['submission_deadline']), 'Thu 23:59')
        self.assertEqual(local(t['matching_at']), 'Fri 09:00')
        self.assertEqual(local(t['window_start']), 'Sun 00:00')
        self.assertEqual(local(t['window_end']), 'Sun 00:00')
        self.assertEqual(t['earliest_session_start'] - t['matching_at'], timedelta(hours=48))
        self.assertEqual(t['window_start'], utc(2026, 10, 4, 4))  # EDT

    def test_t25_dst_weeks_are_167_or_169_hours_and_rounds_touch(self):
        spring = round_times(date(2027, 3, 14))  # US DST starts that Sunday
        fall = round_times(date(2026, 11, 1))    # US DST ends that Sunday
        self.assertEqual(spring['window_end'] - spring['window_start'], timedelta(hours=167))
        self.assertEqual(fall['window_end'] - fall['window_start'], timedelta(hours=169))
        for week in (date(2026, 10, 25), date(2027, 3, 7), date(2027, 3, 14)):
            with self.subTest(week=week):
                this, following = round_times(week), round_times(week + timedelta(days=7))
                self.assertEqual(this['window_end'], following['window_start'])

    def test_deadline_keeps_its_local_time_across_a_dst_change(self):
        before, after = round_times(date(2026, 11, 1)), round_times(date(2026, 11, 8))
        self.assertEqual(local(before['submission_deadline']), 'Thu 23:59')  # EDT
        self.assertEqual(local(after['submission_deadline']), 'Thu 23:59')   # EST
        self.assertEqual(after['submission_deadline'] - before['submission_deadline'], timedelta(days=7, hours=1))

    def test_upcoming_week_keys_are_the_next_sundays(self):
        self.assertEqual(upcoming_week_keys(utc(2026, 10, 20, 12)), [date(2026, 10, 25), date(2026, 11, 1)])
        # On a Sunday the current week has started: the next round is the following Sunday.
        self.assertEqual(upcoming_week_keys(utc(2026, 10, 25, 16))[0], date(2026, 11, 1))
        # Saturday 23:30 in New York is already Sunday in UTC; the ops timezone decides.
        self.assertEqual(upcoming_week_keys(utc(2026, 10, 25, 3, 30))[0], date(2026, 10, 25))

    @override_settings(PEER_MOCK_OPS_TZ='Europe/London')
    def test_ops_timezone_is_a_setting(self):
        t = round_times(date(2026, 10, 4))
        self.assertEqual(t['window_start'], utc(2026, 10, 3, 23))  # 00:00 BST
        self.assertEqual(local(t['submission_deadline'], ZoneInfo('Europe/London')), 'Thu 23:59')

    def test_invalid_ops_timezone_fails_at_startup(self):
        check_settings()  # the configured default is valid
        for bad in ('Mars/Olympus', ''):
            with self.subTest(value=bad), override_settings(PEER_MOCK_OPS_TZ=bad):
                with self.assertRaises(ImproperlyConfigured):
                    check_settings()


class EnsureRoundsTest(TestCase):

    def test_creates_the_next_two_rounds_once(self):
        now = utc(2026, 10, 20, 12)
        self.assertEqual(ensure_rounds(now), [date(2026, 10, 25), date(2026, 11, 1)])
        self.assertEqual(ensure_rounds(now), [])
        self.assertEqual(Round.objects.count(), 2)
        self.assertEqual(PeerEvent.objects.filter(event_type='round_opened').count(), 2)
        rnd = Round.objects.get(week_key=date(2026, 11, 1))
        self.assertEqual(rnd.status, 'open')
        self.assertEqual(rnd.window_start, round_times(date(2026, 11, 1))['window_start'])

    @override_settings(PEER_MOCK_OPS_TZ='Europe/London')
    def test_uses_the_ops_timezone(self):
        ensure_rounds(utc(2026, 10, 20, 12))
        self.assertEqual(Round.objects.get(week_key=date(2026, 10, 25)).window_start, utc(2026, 10, 24, 23))

    def test_current_round_is_the_open_one_with_the_nearest_future_deadline(self):
        first, second = make_round(date(2026, 10, 25)), make_round(date(2026, 11, 1))
        self.assertEqual(current_round(utc(2026, 10, 20, 12)), first)
        self.assertEqual(current_round(first.submission_deadline), second)  # deadline reached
        Round.objects.filter(pk=second.pk).update(status='cancelled')
        self.assertIsNone(current_round(first.submission_deadline))


class EnsureRoundsTaskTest(TestCase):

    def test_task_is_gated_by_peer_mock_bus(self):
        self.assertEqual(ensure_rounds_task.required_bus, 'PEER_MOCK_BUS')
        power_peer_mock(bus='OFF')
        self.assertEqual(ensure_rounds_task.run(), 'skipped: bus off')
        self.assertFalse(Round.objects.exists())
        power_peer_mock(bus='ON')
        self.assertEqual(len(ensure_rounds_task.run()), 2)
