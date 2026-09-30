"""
Weekly round schedule (design doc §5.1).

Schedule points are defined as wall times in the ops timezone
(settings.PEER_MOCK_OPS_TZ) and converted to UTC for their own dates, so they
stay at the same local time across DST changes. The week key is the Sunday
the session window starts; consecutive rounds' windows touch and never
overlap.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .events import emit
from .models import Round
from .timeutil import UTC

LEAD = timedelta(hours=48)  # earliest session start = matching + LEAD
WEEKS_AHEAD = 2

# (days relative to the week key, local time)
SCHEDULE = {
    'invite_at': (-6, time(10, 0)),             # Monday before
    'submission_deadline': (-3, time(23, 59)),  # Thursday before
    'matching_at': (-2, time(9, 0)),            # Friday before
    'window_start': (0, time(0, 0)),            # Sunday
    'window_end': (7, time(0, 0)),              # next Sunday
}


def ops_zone():
    return ZoneInfo(settings.PEER_MOCK_OPS_TZ)


def round_times(week_key, tz=None):
    """UTC schedule points for the round whose window starts on week_key (a Sunday)."""
    tz = tz or ops_zone()
    times = {name: datetime.combine(week_key + timedelta(days=days), at, tzinfo=tz).astimezone(UTC)
             for name, (days, at) in SCHEDULE.items()}
    times['earliest_session_start'] = times['matching_at'] + LEAD
    return times


def upcoming_week_keys(now, weeks=WEEKS_AHEAD, tz=None):
    """The next `weeks` Sundays strictly after today (in the ops timezone)."""
    today = now.astimezone(tz or ops_zone()).date()
    first = today + timedelta(days=(6 - today.weekday()) % 7 or 7)
    return [first + timedelta(weeks=k) for k in range(weeks)]


def ensure_rounds(now=None, weeks=WEEKS_AHEAD):
    """Create the upcoming rounds that do not exist yet. Idempotent; returns the new week keys."""
    now = now or timezone.now()
    tz = ops_zone()
    created = []
    for week_key in upcoming_week_keys(now, weeks, tz):
        with transaction.atomic():
            rnd, is_new = Round.objects.get_or_create(week_key=week_key, defaults=round_times(week_key, tz))
            if is_new:
                emit('round_opened', actor_kind='system', round_id=rnd.id,
                     metadata={'week_key': week_key.isoformat()},
                     idempotency_key=f'round_opened:{week_key.isoformat()}')
                created.append(week_key)
    return created


def current_round(now=None):
    """The open round with the nearest submission deadline still in the future."""
    now = now or timezone.now()
    return (Round.objects.filter(status='open', submission_deadline__gt=now)
            .order_by('submission_deadline').first())
