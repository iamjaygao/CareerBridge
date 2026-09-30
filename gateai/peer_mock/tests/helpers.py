"""Shared fixtures for peer mock tests."""

from contextlib import contextmanager
from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from kernel.governance.models import BusPowerState, FeatureFlag, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache
from peer_mock import invites
from peer_mock.constants import TERMS_VERSION
from peer_mock.models import PeerProfile, Round
from peer_mock.rounds import round_times

User = get_user_model()
UTC = dt_timezone.utc

# A fixed "now" for API tests: Tuesday 2026-10-20 12:00Z. The round of week
# 2026-11-01 (US DST ends that Sunday) is open: its deadline is Thu Oct 29.
NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
WEEK = datetime(2026, 11, 1).date()


def power_peer_mock(bus='ON', flag='ON'):
    BusPowerState.objects.all().delete()
    BusPowerState.objects.bulk_create(
        [BusPowerState(bus_name=n, state=s) for n, s in {**BUS_POWER_DEFAULTS, 'PEER_MOCK_BUS': bus}.items()])
    if not PlatformState.objects.exists():
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=['PEER_MOCK'], frozen_modules=[],
                                     reason='t')
    FeatureFlag.objects.update_or_create(key='PEER_MOCK', defaults={'state': flag, 'visibility': 'user',
                                                                    'reason': 't'})
    invalidate_cache()
    cache.clear()  # throttle counters


def make_user(name, verified=True, **extra):
    return User.objects.create_user(username=name, email=f'{name}@example.com', password='Passw0rd!x',
                                    email_verified=verified, **extra)


def client_for(user):
    client = APIClient()
    if user is not None:
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
    return client


def onboard(user, tz='America/New_York', name=None):
    return PeerProfile.objects.create(user=user, display_name=name or user.username.title(), timezone=tz,
                                      terms_version=TERMS_VERSION, terms_accepted_at=NOW, adult_confirmed_at=NOW)


def make_round(week_key=WEEK, **overrides):
    return Round.objects.create(week_key=week_key, **{**round_times(week_key), **overrides})


def make_invite(label='cohort-1', max_uses=10, **kwargs):
    invite, code = invites.create(label, max_uses, **kwargs)
    return invite, code


def onboarding_body(**overrides):
    body = {'display_name': 'Alex', 'timezone': 'America/New_York', 'email_round_invites': False,
            'share_email_with_partner': False, 'accept_terms_version': TERMS_VERSION, 'confirm_adult': True}
    body.update(overrides)
    return body


@contextmanager
def frozen(now=NOW):
    with mock.patch('django.utils.timezone.now', return_value=now):
        yield


def utc(*args):
    return datetime(*args, tzinfo=UTC)


__all__ = ['NOW', 'WEEK', 'User', 'client_for', 'frozen', 'make_invite', 'make_round', 'make_user', 'onboard',
           'onboarding_body', 'power_peer_mock', 'timezone', 'utc']
