"""
Local wall time <-> UTC, per concrete calendar date (design doc §2.3, §3.7).

Rules:
- Everything is stored in UTC. A local time is converted with zoneinfo for its
  own date, never as "weekday + fixed offset", so DST is handled per date.
- A local time inside a spring-forward gap does not exist: it is rejected.
- A local time repeated at fall-back is ambiguous: the first occurrence
  (fold=0) is used and a warning is returned so the UI can echo it.
- Nothing here reads the clock or the machine's timezone.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones

from .constants import GRANULARITY_MINUTES, MAX_WINDOW_MINUTES, MAX_WINDOWS, MIN_WINDOW_MINUTES

UTC = timezone.utc


class LocalTimeError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@lru_cache(maxsize=1)
def _timezone_names():
    return frozenset(available_timezones())


def get_zone(name):
    """The ZoneInfo for an IANA name, or LocalTimeError('invalid_timezone')."""
    if not isinstance(name, str) or name not in _timezone_names():
        raise LocalTimeError('invalid_timezone', f'{name!r} is not a valid IANA timezone')
    return ZoneInfo(name)


def local_to_utc(naive, tz):
    """
    Convert a naive local datetime to an aware UTC datetime.

    Returns (utc, warning_code). Raises LocalTimeError('nonexistent_local_time')
    for a time inside a DST gap; warning_code is 'ambiguous_local_time' for a
    time that occurs twice (resolved to its first occurrence).
    """
    first = naive.replace(tzinfo=tz, fold=0)
    utc = first.astimezone(UTC)
    if utc.astimezone(tz).replace(tzinfo=None) != naive:
        raise LocalTimeError(
            'nonexistent_local_time',
            f'{naive:%Y-%m-%d %H:%M} does not exist in {tz.key} (clocks move forward)')
    second = naive.replace(tzinfo=tz, fold=1).astimezone(UTC)
    return utc, ('ambiguous_local_time' if second != utc else None)


def format_local(utc, tz):
    """'Tue Mar 10, 19:00 EDT' for an aware datetime shown in tz."""
    local = utc.astimezone(tz)
    return f'{local:%a %b} {local.day}, {local:%H:%M} {local.tzname()}'


def format_range(start_utc, end_utc, tz):
    """'2026-03-10 18:00–20:00 EDT', or both dates/abbreviations when they differ."""
    s, e = start_utc.astimezone(tz), end_utc.astimezone(tz)
    if s.date() == e.date() and s.tzname() == e.tzname():
        return f'{s:%Y-%m-%d %H:%M}–{e:%H:%M} {s.tzname()}'
    return f'{s:%Y-%m-%d %H:%M} {s.tzname()} – {e:%Y-%m-%d %H:%M} {e.tzname()}'


@dataclass(frozen=True)
class Window:
    start_utc: datetime
    end_utc: datetime
    local_start: str  # 'YYYY-MM-DDTHH:MM' as the user typed it
    local_end: str


def _parse_hhmm(value, field):
    try:
        parsed = time.fromisoformat(value)
    except (TypeError, ValueError):
        raise LocalTimeError('invalid_time', f'{field} must be HH:MM')
    if parsed.second or parsed.microsecond or parsed.minute % GRANULARITY_MINUTES:
        raise LocalTimeError('invalid_time', f'{field} must be on a {GRANULARITY_MINUTES}-minute step')
    return parsed


def parse_window(raw, tz):
    """
    Convert {'date': 'YYYY-MM-DD', 'start': 'HH:MM', 'end': 'HH:MM'} in tz to a Window.

    end <= start means the window ends on the next day. Returns (window, warnings).
    """
    if not isinstance(raw, dict):
        raise LocalTimeError('invalid_window', 'each window needs date, start and end')
    try:
        day = date.fromisoformat(raw.get('date'))
    except (TypeError, ValueError):
        raise LocalTimeError('invalid_date', 'date must be YYYY-MM-DD')
    start_t = _parse_hhmm(raw.get('start'), 'start')
    end_t = _parse_hhmm(raw.get('end'), 'end')
    start_local = datetime.combine(day, start_t)
    end_local = datetime.combine(day + timedelta(days=1) if end_t <= start_t else day, end_t)

    start_utc, w1 = local_to_utc(start_local, tz)
    end_utc, w2 = local_to_utc(end_local, tz)
    minutes = (end_utc - start_utc) / timedelta(minutes=1)
    if minutes < MIN_WINDOW_MINUTES:
        raise LocalTimeError('window_too_short', f'a window must be at least {MIN_WINDOW_MINUTES} minutes')
    if minutes > MAX_WINDOW_MINUTES:
        raise LocalTimeError('window_too_long', f'a window must be at most {MAX_WINDOW_MINUTES // 60} hours')
    warnings = [code for code in (w1, w2) if code]
    return Window(start_utc, end_utc, f'{start_local:%Y-%m-%dT%H:%M}', f'{end_local:%Y-%m-%dT%H:%M}'), warnings


def convert_windows(raw_windows, tz, clip_start, clip_end, min_minutes=MIN_WINDOW_MINUTES):
    """
    Validate, convert, clip to [clip_start, clip_end) and merge a list of raw windows.

    Returns (windows, warnings, errors). warnings/errors are lists of
    {'window': index, 'code': ..., 'message': ...}; when errors is non-empty the
    submission must be rejected as a whole.
    """
    if not isinstance(raw_windows, list) or not raw_windows:
        return [], [], [{'window': None, 'code': 'no_windows', 'message': 'submit at least one window'}]
    if len(raw_windows) > MAX_WINDOWS:
        return [], [], [{'window': None, 'code': 'too_many_windows',
                         'message': f'at most {MAX_WINDOWS} windows per round'}]

    converted, warnings, errors = [], [], []
    for index, raw in enumerate(raw_windows):
        try:
            window, codes = parse_window(raw, tz)
        except LocalTimeError as exc:
            errors.append({'window': index, 'code': exc.code, 'message': exc.message})
            continue
        for code in codes:
            warnings.append({'window': index, 'code': code, 'message':
                             'a local time occurs twice here; the first occurrence was used '
                             f'({format_range(window.start_utc, window.end_utc, tz)})'})
        start, end = max(window.start_utc, clip_start), min(window.end_utc, clip_end)
        if (end - start) < timedelta(minutes=min_minutes):
            errors.append({'window': index, 'code': 'outside_round',
                           'message': f'less than {min_minutes} minutes of this window fall inside the round'})
            continue
        if (start, end) != (window.start_utc, window.end_utc):
            warnings.append({'window': index, 'code': 'clipped',
                             'message': 'the part outside the round (or before the earliest start) was removed'})
            window = Window(start, end, _local_str(start, tz), _local_str(end, tz))
        converted.append(window)
    if errors:
        return [], warnings, errors
    return merge_windows(converted, tz), warnings, []


def _local_str(utc, tz):
    return f'{utc.astimezone(tz):%Y-%m-%dT%H:%M}'


def merge_windows(windows, tz):
    """Sort by start and merge overlapping or touching windows."""
    merged = []
    for w in sorted(windows, key=lambda w: (w.start_utc, w.end_utc)):
        if merged and w.start_utc <= merged[-1].end_utc:
            last = merged[-1]
            if w.end_utc > last.end_utc:
                merged[-1] = Window(last.start_utc, w.end_utc, last.local_start, _local_str(w.end_utc, tz))
        else:
            merged.append(w)
    return merged
