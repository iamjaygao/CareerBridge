"""
Local time <-> UTC conversion, per date and DST-safe (design doc §3.7, §8.4).

T9–T12b and T23 of the design; the matching parts of T11/T12 (overlap and
slot alignment) are tested with the matcher in PR2.
"""

import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from peer_mock.constants import MAX_WINDOWS
from peer_mock.timeutil import (LocalTimeError, convert_windows, format_local, get_zone, local_to_utc,
                                parse_window)

from .helpers import utc

NY, LONDON = ZoneInfo('America/New_York'), ZoneInfo('Europe/London')
FAR_PAST, FAR_FUTURE = utc(2000, 1, 1), utc(2100, 1, 1)


def window(day, start, end):
    return {'date': day, 'start': start, 'end': end}


class LocalToUtcTest(SimpleTestCase):

    def test_t9_spring_forward_gap_is_rejected(self):
        with self.assertRaises(LocalTimeError) as ctx:
            local_to_utc(datetime(2026, 3, 8, 2, 30), NY)
        self.assertEqual(ctx.exception.code, 'nonexistent_local_time')
        self.assertIn('2026-03-08 02:30', ctx.exception.message)

    def test_t10_fall_back_ambiguity_uses_first_occurrence(self):
        self.assertEqual(local_to_utc(datetime(2026, 11, 1, 1, 30), NY),
                         (utc(2026, 11, 1, 5, 30), 'ambiguous_local_time'))

    def test_ordinary_time_has_no_warning(self):
        self.assertEqual(local_to_utc(datetime(2026, 7, 1, 9, 0), NY), (utc(2026, 7, 1, 13, 0), None))

    def test_invalid_timezone(self):
        for name in ('Mars/Olympus', '', None, 'EST5EDT '):
            with self.subTest(name=name), self.assertRaises(LocalTimeError) as ctx:
                get_zone(name)
            self.assertEqual(ctx.exception.code, 'invalid_timezone')


class ParseWindowTest(SimpleTestCase):

    def test_t11_new_york_and_london_on_the_same_date(self):
        # 2026-03-10: the US is already on DST, the UK is not.
        ny, _ = parse_window(window('2026-03-10', '18:00', '20:00'), NY)
        ldn, _ = parse_window(window('2026-03-10', '23:00', '01:00'), LONDON)  # ends next day
        self.assertEqual((ny.start_utc, ny.end_utc), (utc(2026, 3, 10, 22), utc(2026, 3, 11, 0)))
        self.assertEqual((ldn.start_utc, ldn.end_utc), (utc(2026, 3, 10, 23), utc(2026, 3, 11, 1)))
        self.assertEqual(ldn.local_end, '2026-03-11T01:00')

    def test_t12_kolkata_half_hour_offset(self):
        w, _ = parse_window(window('2026-03-10', '10:00', '11:30'), ZoneInfo('Asia/Kolkata'))
        self.assertEqual((w.start_utc, w.end_utc), (utc(2026, 3, 10, 4, 30), utc(2026, 3, 10, 6, 0)))

    def test_t12b_kathmandu_quarter_hour_offset(self):
        w, _ = parse_window(window('2026-03-10', '10:00', '11:00'), ZoneInfo('Asia/Kathmandu'))
        self.assertEqual((w.start_utc, w.end_utc), (utc(2026, 3, 10, 4, 15), utc(2026, 3, 10, 5, 15)))

    def test_t23_windows_across_dst_changes_have_their_real_length(self):
        fall, _ = parse_window(window('2026-11-01', '00:30', '02:30'), NY)
        self.assertEqual((fall.start_utc, fall.end_utc), (utc(2026, 11, 1, 4, 30), utc(2026, 11, 1, 7, 30)))
        self.assertEqual(fall.end_utc - fall.start_utc, timedelta(hours=3))
        spring, _ = parse_window(window('2026-03-08', '01:00', '04:00'), NY)
        self.assertEqual((spring.start_utc, spring.end_utc), (utc(2026, 3, 8, 6), utc(2026, 3, 8, 8)))
        self.assertEqual(spring.end_utc - spring.start_utc, timedelta(hours=2))

    def test_times_must_be_on_a_15_minute_step(self):
        for start in ('18:10', '18:00:30', 'six', None):
            with self.subTest(start=start), self.assertRaises(LocalTimeError) as ctx:
                parse_window(window('2026-03-10', start, '20:00'), NY)
            self.assertEqual(ctx.exception.code, 'invalid_time')

    def test_length_limits(self):
        for (start, end), code in {('18:00', '18:45'): 'window_too_short',
                                   ('06:00', '18:15'): 'window_too_long'}.items():
            with self.subTest(code=code), self.assertRaises(LocalTimeError) as ctx:
                parse_window(window('2026-03-10', start, end), NY)
            self.assertEqual(ctx.exception.code, code)

    def test_bad_date(self):
        with self.assertRaises(LocalTimeError) as ctx:
            parse_window(window('10/03/2026', '18:00', '20:00'), NY)
        self.assertEqual(ctx.exception.code, 'invalid_date')


class ConvertWindowsTest(SimpleTestCase):

    def convert(self, raw, clip_start=FAR_PAST, clip_end=FAR_FUTURE, tz=NY):
        return convert_windows(raw, tz, clip_start, clip_end)

    def test_overlapping_and_touching_windows_are_merged(self):
        windows, warnings, errors = self.convert([
            window('2026-07-01', '18:00', '20:00'), window('2026-07-01', '19:00', '21:00'),
            window('2026-07-01', '21:00', '22:00'), window('2026-07-02', '09:00', '10:00')])
        self.assertEqual(errors, [])
        self.assertEqual([(w.start_utc, w.end_utc) for w in windows],
                         [(utc(2026, 7, 1, 22), utc(2026, 7, 2, 2)), (utc(2026, 7, 2, 13), utc(2026, 7, 2, 14))])

    def test_clipping_is_reported_and_short_remainders_rejected(self):
        clip_start = utc(2026, 7, 1, 23)  # 19:00 EDT
        windows, warnings, errors = self.convert([window('2026-07-01', '18:00', '21:00')], clip_start)
        self.assertEqual([(w.start_utc, w.end_utc) for w in windows], [(utc(2026, 7, 1, 23), utc(2026, 7, 2, 1))])
        self.assertEqual([w['code'] for w in warnings], ['clipped'])
        _, _, errors = self.convert([window('2026-07-01', '18:00', '19:30')], clip_start)
        self.assertEqual([e['code'] for e in errors], ['outside_round'])

    def test_any_error_rejects_the_whole_submission(self):
        windows, _, errors = self.convert([window('2026-07-01', '18:00', '20:00'),
                                           window('2027-03-14', '02:30', '04:00')])
        self.assertEqual(windows, [])
        self.assertEqual(errors, [{'window': 1, 'code': 'nonexistent_local_time', 'message': errors[0]['message']}])

    def test_ambiguous_time_is_echoed_as_a_warning(self):
        windows, warnings, errors = self.convert([window('2026-11-01', '01:30', '03:00')])
        self.assertEqual(errors, [])
        self.assertEqual(windows[0].start_utc, utc(2026, 11, 1, 5, 30))
        self.assertEqual([w['code'] for w in warnings], ['ambiguous_local_time'])
        self.assertIn('EDT', warnings[0]['message'])

    def test_window_count_limit(self):
        raw = [window('2026-07-01', '00:00', '01:00')] * (MAX_WINDOWS + 1)
        self.assertEqual([e['code'] for e in self.convert(raw)[2]], ['too_many_windows'])
        self.assertEqual([e['code'] for e in self.convert([])[2]], ['no_windows'])


class DisplayTest(SimpleTestCase):

    def test_one_instant_in_four_timezones(self):
        instant = utc(2026, 3, 10, 23, 0)
        expected = {
            'America/New_York': 'Tue Mar 10, 19:00 EDT',
            'Europe/London': 'Tue Mar 10, 23:00 GMT',
            'Asia/Shanghai': 'Wed Mar 11, 07:00 CST',
            'Asia/Kolkata': 'Wed Mar 11, 04:30 IST',
        }
        for name, text in expected.items():
            with self.subTest(tz=name):
                self.assertEqual(format_local(instant, ZoneInfo(name)), text)

    def test_results_do_not_depend_on_the_machine_timezone(self):
        def sample():
            w, _ = parse_window(window('2026-03-10', '18:00', '20:00'), NY)
            return w, format_local(w.start_utc, LONDON)

        baseline = sample()
        original = os.environ.get('TZ')
        try:
            for machine_tz in ('Asia/Tokyo', 'Pacific/Auckland', 'UTC'):
                os.environ['TZ'] = machine_tz
                time.tzset()
                with self.subTest(machine_tz=machine_tz):
                    self.assertEqual(sample(), baseline)
        finally:
            if original is None:
                os.environ.pop('TZ', None)
            else:
                os.environ['TZ'] = original
            time.tzset()
