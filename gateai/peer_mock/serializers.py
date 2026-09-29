"""Serializers for peer mock profile, rounds and registrations (design doc §2.2, §2.3)."""

import unicodedata

from rest_framework import serializers

from .constants import DIRECTIONS, DISPLAY_NAME_MAX, INTERVIEW_TYPES
from .models import PeerProfile
from .timeutil import LocalTimeError, format_local, format_range, get_zone


def validate_direction(interview_type, direction):
    if direction and direction not in DIRECTIONS.get(interview_type, ()):
        raise serializers.ValidationError(
            {'direction': f'{direction!r} is not a direction of {interview_type!r}'})


class ProfileWriteSerializer(serializers.Serializer):
    """PUT me/profile/. Identity comes from request.user only; any user field is ignored."""

    display_name = serializers.CharField(max_length=DISPLAY_NAME_MAX, trim_whitespace=True)
    timezone = serializers.CharField(max_length=64)
    default_interview_type = serializers.ChoiceField(choices=INTERVIEW_TYPES, required=False, allow_blank=True)
    default_direction = serializers.CharField(max_length=24, required=False, allow_blank=True)
    email_round_invites = serializers.BooleanField()
    share_email_with_partner = serializers.BooleanField()
    accept_terms_version = serializers.CharField(max_length=16, required=False, allow_blank=True)
    confirm_adult = serializers.BooleanField(required=False, default=False)
    invite_code = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_display_name(self, value):
        if any(unicodedata.category(ch).startswith('C') for ch in value):
            raise serializers.ValidationError('must not contain control characters')
        return value

    def validate_timezone(self, value):
        try:
            get_zone(value)
        except LocalTimeError as exc:
            raise serializers.ValidationError(exc.message)
        return value

    def validate(self, attrs):
        validate_direction(attrs.get('default_interview_type') or '', attrs.get('default_direction') or '')
        return attrs


def profile_data(profile):
    return {
        'display_name': profile.display_name,
        'timezone': profile.timezone,
        'default_interview_type': profile.default_interview_type,
        'default_direction': profile.default_direction,
        'email_round_invites': profile.email_round_invites,
        'share_email_with_partner': profile.share_email_with_partner,
        'terms_version': profile.terms_version,
        'reputation': {
            'completed': profile.completed_count,
            'no_shows': profile.no_show_count,
            'late_cancels': profile.late_cancel_count,
            'disputes': profile.dispute_count,
            'needs_review': profile.needs_review,
        },
    }


class RegistrationWriteSerializer(serializers.Serializer):
    interview_type = serializers.ChoiceField(choices=INTERVIEW_TYPES)
    direction = serializers.CharField(max_length=24, required=False, allow_blank=True, default='')
    windows = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate(self, attrs):
        validate_direction(attrs['interview_type'], attrs['direction'])
        return attrs


ROUND_TIME_FIELDS = ('submission_deadline', 'matching_at', 'window_start', 'window_end', 'earliest_session_start')


def round_data(rnd, tz):
    data = {'id': str(rnd.public_id), 'status': rnd.status, 'week_key': rnd.week_key.isoformat(),
            'session_minutes': rnd.session_minutes}
    for field in ROUND_TIME_FIELDS:
        value = getattr(rnd, field)
        data[field] = value.isoformat().replace('+00:00', 'Z')
        data[f'{field}_local'] = format_local(value, tz)
    return data


def registration_data(registration, tz):
    return {
        'round_id': str(registration.round.public_id),
        'status': registration.status,
        'interview_type': registration.interview_type,
        'direction': registration.direction,
        'windows': [{
            'local': format_range(w.start_utc, w.end_utc, tz),
            'start_utc': w.start_utc.isoformat().replace('+00:00', 'Z'),
            'end_utc': w.end_utc.isoformat().replace('+00:00', 'Z'),
            'submitted': {'local_start': w.local_start, 'local_end': w.local_end, 'tz': w.tz_name},
        } for w in registration.windows.all()],
    }
