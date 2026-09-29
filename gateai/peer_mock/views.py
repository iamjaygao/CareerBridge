"""
Peer mock API views.

The health/status/sessions stubs stay until PR2 (sessions) and the LATER
dedicated FeatureVisibility test endpoint (health/status). The rest is the
PR1 API: profile, meta, current round, registration (design doc §2.2, §2.3).
Every view acts on request.user only; no endpoint takes a user id.
"""

from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kernel.governance.permissions import FeatureVisibility

from .constants import DIRECTIONS, GRANULARITY_MINUTES, INTERVIEW_TYPES, MAX_WINDOWS, MIN_WINDOW_MINUTES, TERMS_VERSION
from .events import attach_actor_ref, emit
from .invites import consume as consume_invite
from .models import AvailabilityWindow, PeerProfile, PreRegistration, Registration, Round
from .permissions import PEER_BASE, PEER_ONBOARDED, PEER_THROTTLES, InviteCodeThrottle, error
from .rounds import current_round
from .serializers import (ProfileWriteSerializer, RegistrationWriteSerializer, profile_data, registration_data,
                          round_data)
from .timeutil import convert_windows, get_zone


class PeerMockHealthView(APIView):
    permission_classes = [IsAuthenticated, FeatureVisibility]
    
    def get(self, request):
        return Response({
            "ok": True,
            "service": "peer_mock",
            "ts": timezone.now().isoformat()
        })


class PeerMockStatusView(APIView):
    permission_classes = [IsAuthenticated, FeatureVisibility]
    
    def get(self, request):
        return Response({
            "bus": "PEER_MOCK_BUS",
            "state": "ON",
            "ts": timezone.now().isoformat()
        })


class PeerMockSessionsView(APIView):
    permission_classes = [IsAuthenticated, FeatureVisibility]

    def get(self, request):
        return Response([])


# ── PR1 API ───────────────────────────────────────────────────────────────────

PROFILE_FIELDS = ('display_name', 'timezone', 'default_interview_type', 'default_direction',
                  'email_round_invites', 'share_email_with_partner')


def _prefill(user):
    pre = PreRegistration.objects.filter(email__iexact=user.email, claimed_by__isnull=True).first()
    if pre is None:
        return None
    return {'display_name': pre.display_name, 'timezone': pre.timezone,
            'default_interview_type': pre.interview_type, 'default_direction': pre.direction}


class MetaView(APIView):
    permission_classes = PEER_BASE
    throttle_classes = PEER_THROTTLES

    def get(self, request):
        return Response({
            'interview_types': list(INTERVIEW_TYPES),
            'directions': {k: list(v) for k, v in DIRECTIONS.items()},
            'terms_version': TERMS_VERSION,
            'invite_required': settings.PEER_MOCK_INVITE_REQUIRED,
            'limits': {'max_windows': MAX_WINDOWS, 'min_window_minutes': MIN_WINDOW_MINUTES,
                       'granularity_minutes': GRANULARITY_MINUTES},
        })


class ProfileView(APIView):
    """GET/PUT me/profile/. The first PUT is onboarding."""

    permission_classes = PEER_BASE
    throttle_classes = PEER_THROTTLES + [InviteCodeThrottle]

    def get(self, request):
        profile = PeerProfile.objects.filter(user=request.user).first()
        if profile is None:
            body = error('No peer mock profile yet.', 'no_profile')
            body['prefill'] = _prefill(request.user)
            return Response(body, status=status.HTTP_404_NOT_FOUND)
        return Response(profile_data(profile))

    def put(self, request):
        serializer = ProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        now = timezone.now()
        try:
            with transaction.atomic():
                profile = PeerProfile.objects.select_for_update().filter(user=request.user).first()
                if profile is None:
                    return self._onboard(request, data, now)
                for field in PROFILE_FIELDS:
                    if field in data:
                        setattr(profile, field, data[field])
                if data.get('accept_terms_version') == TERMS_VERSION and profile.terms_version != TERMS_VERSION:
                    profile.terms_version, profile.terms_accepted_at = TERMS_VERSION, now
                profile.save()
        except IntegrityError:  # a concurrent first PUT created the profile
            return Response(error('Profile was just created; retry.', 'conflict'), status=status.HTTP_409_CONFLICT)
        return Response(profile_data(profile))

    def _onboard(self, request, data, now):
        if data.get('accept_terms_version') != TERMS_VERSION:
            return Response(error('Accept the current terms and privacy notice.', 'terms_not_accepted'),
                            status=status.HTTP_400_BAD_REQUEST)
        if not data.get('confirm_adult'):
            return Response(error('You must be at least 18 years old to use peer mock.',
                                  'adult_confirmation_required'), status=status.HTTP_400_BAD_REQUEST)
        invite = None
        if settings.PEER_MOCK_INVITE_REQUIRED:
            invite = consume_invite(data.get('invite_code'), now)
            if invite is None:
                return Response(error('This invite code is not valid.', 'invalid_invite_code'),
                                status=status.HTTP_400_BAD_REQUEST)
        profile = PeerProfile.objects.create(
            user=request.user, invite_code=invite, terms_version=TERMS_VERSION, terms_accepted_at=now,
            adult_confirmed_at=now, **{f: data[f] for f in PROFILE_FIELDS if f in data})
        PreRegistration.objects.filter(email__iexact=request.user.email, claimed_by__isnull=True) \
            .update(claimed_by=request.user)
        attach_actor_ref(profile)
        emit('onboarded', user=request.user, metadata={'invite_label': invite.label if invite else None},
             idempotency_key=f'onboarded:{request.user.pk}')
        return Response(profile_data(profile), status=status.HTTP_201_CREATED)


class CurrentRoundView(APIView):
    permission_classes = PEER_ONBOARDED
    throttle_classes = PEER_THROTTLES

    def get(self, request):
        tz = get_zone(request.user.peer_profile.timezone)
        rnd = current_round()
        if rnd is None:
            return Response(error('The next round opens soon.', 'no_open_round'), status=status.HTTP_404_NOT_FOUND)
        data = round_data(rnd, tz)
        registration = Registration.objects.filter(round=rnd, user=request.user).first()
        data['my_registration'] = registration_data(registration, tz) if registration else None
        return Response(data)


class RegistrationView(APIView):
    """GET/PUT/DELETE rounds/<id>/registration/: the caller's own registration only."""

    permission_classes = PEER_ONBOARDED
    throttle_classes = PEER_THROTTLES

    def _round(self, round_id):
        return get_object_or_404(Round, public_id=round_id)

    @staticmethod
    def _closed(rnd):
        return rnd.status != 'open' or timezone.now() >= rnd.submission_deadline

    def get(self, request, round_id):
        rnd = self._round(round_id)
        registration = get_object_or_404(Registration, round=rnd, user=request.user)
        return Response(registration_data(registration, get_zone(request.user.peer_profile.timezone)))

    def put(self, request, round_id):
        rnd = self._round(round_id)
        if self._closed(rnd):
            return Response(error('Submissions for this round are closed.', 'round_closed'),
                            status=status.HTTP_409_CONFLICT)
        serializer = RegistrationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        tz_name = request.user.peer_profile.timezone
        tz = get_zone(tz_name)
        windows, warnings, errors = convert_windows(
            data['windows'], tz, rnd.earliest_session_start, rnd.window_end, rnd.session_minutes)
        if errors:
            return Response({'windows': errors, 'warnings': warnings}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            Registration.objects.get_or_create(round=rnd, user=request.user,
                                               defaults={'interview_type': data['interview_type']})
            registration = Registration.objects.select_for_update().get(round=rnd, user=request.user)
            registration.interview_type = data['interview_type']
            registration.direction = data['direction']
            registration.status = 'active'
            registration.save()
            registration.windows.all().delete()
            AvailabilityWindow.objects.bulk_create([
                AvailabilityWindow(registration=registration, start_utc=w.start_utc, end_utc=w.end_utc,
                                   local_start=w.local_start, local_end=w.local_end, tz_name=tz_name)
                for w in windows])
            minutes = sum(int((w.end_utc - w.start_utc).total_seconds() // 60) for w in windows)
            emit('availability_submitted', user=request.user, round_id=rnd.id,
                 metadata={'interview_type': data['interview_type'], 'windows': len(windows),
                           'total_minutes': minutes})
        body = registration_data(registration, tz)
        body['warnings'] = warnings
        return Response(body)

    def delete(self, request, round_id):
        rnd = self._round(round_id)
        if self._closed(rnd):
            return Response(error('Submissions for this round are closed.', 'round_closed'),
                            status=status.HTTP_409_CONFLICT)
        with transaction.atomic():
            registration = get_object_or_404(
                Registration.objects.select_for_update(), round=rnd, user=request.user)
            if registration.status != 'withdrawn':
                registration.status = 'withdrawn'
                registration.save(update_fields=['status', 'updated_at'])
                registration.windows.all().delete()  # no longer needed
                emit('registration_withdrawn', user=request.user, round_id=rnd.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
