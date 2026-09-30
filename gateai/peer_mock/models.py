"""
Peer mock data model, PR1 part (design doc §1.1): invite codes, profiles,
weekly rounds, registrations with availability windows, pre-registrations and
the event log. Sessions and participants arrive in PR2.

All times are stored in UTC (USE_TZ=True).
"""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .constants import DISPLAY_NAME_MAX

INTERVIEW_TYPE_CHOICES = [
    ('coding', 'Coding'),
    ('behavioral', 'Behavioral'),
    ('system_design', 'System design'),
]


class InviteCode(models.Model):
    """Invite codes for the first cohort. Only the sha256 of a code is stored."""

    code_hash = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=64)
    max_uses = models.PositiveIntegerField()
    uses = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(uses__lte=F('max_uses')), name='peer_invite_uses_within_max'),
        ]

    def __str__(self):
        return f'{self.label} ({self.uses}/{self.max_uses})'


class Round(models.Model):
    """One weekly round. Schedule points are derived from the ops timezone (rounds.py)."""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('matching', 'Matching'),
        ('matched', 'Matched'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    week_key = models.DateField(unique=True, help_text='Date the session window starts, in the ops timezone')
    invite_at = models.DateTimeField()
    submission_deadline = models.DateTimeField()
    matching_at = models.DateTimeField()
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    earliest_session_start = models.DateTimeField()
    session_minutes = models.PositiveSmallIntegerField(default=60)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='open')
    matched_at = models.DateTimeField(null=True, blank=True)
    algorithm_version = models.CharField(max_length=32, blank=True, default='')
    input_digest = models.CharField(max_length=64, blank=True, default='')
    invites_enqueued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['week_key']
        indexes = [models.Index(fields=['status', 'matching_at'])]
        constraints = [
            models.CheckConstraint(condition=Q(window_start__lt=F('window_end')), name='peer_round_window_order'),
            models.CheckConstraint(condition=Q(submission_deadline__lte=F('matching_at')),
                                   name='peer_round_deadline_before_matching'),
            models.CheckConstraint(condition=Q(matching_at__lte=F('earliest_session_start')),
                                   name='peer_round_matching_before_sessions'),
        ]

    def __str__(self):
        return f'Round {self.week_key} ({self.status})'


class PeerProfile(models.Model):
    """A user's peer mock profile (one-to-one with User), created at onboarding."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
                                related_name='peer_profile')
    actor_ref = models.UUIDField(default=uuid.uuid4, unique=True, editable=False,
                                 help_text='Pseudonymous id used by the event log')
    invite_code = models.ForeignKey(InviteCode, null=True, blank=True, on_delete=models.SET_NULL)
    display_name = models.CharField(max_length=DISPLAY_NAME_MAX)
    timezone = models.CharField(max_length=64)
    default_interview_type = models.CharField(max_length=16, choices=INTERVIEW_TYPE_CHOICES, blank=True, default='')
    default_direction = models.CharField(max_length=24, blank=True, default='')
    email_round_invites = models.BooleanField(default=False)
    share_email_with_partner = models.BooleanField(default=False)
    terms_version = models.CharField(max_length=16)
    terms_accepted_at = models.DateTimeField()
    adult_confirmed_at = models.DateTimeField()
    completed_count = models.PositiveIntegerField(default=0)
    no_show_count = models.PositiveIntegerField(default=0)
    late_cancel_count = models.PositiveIntegerField(default=0)
    dispute_count = models.PositiveIntegerField(default=0)
    suspended_until_round = models.ForeignKey(Round, null=True, blank=True, on_delete=models.SET_NULL,
                                              related_name='+')
    needs_review = models.BooleanField(default=False)
    email_bouncing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class Registration(models.Model):
    """A user's entry into one round."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('withdrawn', 'Withdrawn'),
        ('matched', 'Matched'),
        ('unmatched', 'Unmatched'),
        ('partner_cancelled', 'Partner cancelled'),
        ('dropped', 'Dropped (did not confirm)'),
    ]

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='peer_registrations')
    interview_type = models.CharField(max_length=16, choices=INTERVIEW_TYPE_CHOICES)
    direction = models.CharField(max_length=24, blank=True, default='')
    standby_ok = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['round', 'user'], name='peer_one_registration_per_round')]
        indexes = [models.Index(fields=['round', 'interview_type', 'status'])]


class AvailabilityWindow(models.Model):
    """One availability window; start/end in UTC are what matching uses."""

    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='windows')
    start_utc = models.DateTimeField()
    end_utc = models.DateTimeField()
    # As the user typed it ('YYYY-MM-DDTHH:MM' wall time in tz_name), for echoing back.
    local_start = models.CharField(max_length=16)
    local_end = models.CharField(max_length=16)
    tz_name = models.CharField(max_length=64)

    class Meta:
        ordering = ['start_utc']
        indexes = [models.Index(fields=['registration', 'start_utc'])]
        constraints = [
            models.CheckConstraint(condition=Q(start_utc__lt=F('end_utc')), name='peer_window_order'),
        ]


class PreRegistration(models.Model):
    """A row imported from the pre-registration form, used only to prefill onboarding."""

    email = models.EmailField(unique=True)  # stored lower-case
    display_name = models.CharField(max_length=DISPLAY_NAME_MAX, blank=True, default='')
    interview_type = models.CharField(max_length=16, choices=INTERVIEW_TYPE_CHOICES, blank=True, default='')
    direction = models.CharField(max_length=24, blank=True, default='')
    timezone = models.CharField(max_length=64, blank=True, default='')
    consent_at = models.DateTimeField(null=True, blank=True)
    invited_at = models.DateTimeField(null=True, blank=True)
    claimed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)


class PeerEvent(models.Model):
    """
    Append-only event log for launch metrics (design doc §6).

    No PII in metadata. `user` is nulled on account deletion; `actor_ref`
    stays so per-person metrics survive without identifying anyone.
    """

    ACTOR_KINDS = [('user', 'User'), ('system', 'System'), ('admin', 'Admin')]

    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    event_type = models.CharField(max_length=40)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='+')
    actor_ref = models.UUIDField(null=True, blank=True)
    actor_kind = models.CharField(max_length=8, choices=ACTOR_KINDS, default='user')
    round_id = models.BigIntegerField(null=True, blank=True)
    session_id = models.BigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'occurred_at']),
            models.Index(fields=['actor_ref', 'occurred_at']),
            models.Index(fields=['round_id', 'event_type']),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.occurred_at:%Y-%m-%d %H:%M}'
