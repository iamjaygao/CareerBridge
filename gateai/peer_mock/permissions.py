"""
DRF permission classes and throttles for peer mock endpoints (design doc §2.1).

Every peer mock view declares its permission_classes explicitly. FeatureVisibility
runs before the peer mock checks, so a hidden feature stays a 404 for everyone.
"""

from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from kernel.governance.permissions import FeatureVisibility

from .models import PeerProfile


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflict.'
    default_code = 'conflict'


def error(message, code):
    """Body shape for peer mock errors: {"detail": ..., "code": ...}."""
    return {'detail': message, 'code': code}


class IsEmailVerified(BasePermission):
    """Peer mock is only for users who verified their email address."""

    def has_permission(self, request, view):
        if not getattr(request.user, 'email_verified', False):
            raise PermissionDenied(error('Verify your email address to use peer mock.', 'email_not_verified'))
        return True


class HasPeerProfile(BasePermission):
    """Onboarding (PUT me/profile/) must be completed first."""

    def has_permission(self, request, view):
        if not PeerProfile.objects.filter(user=request.user).exists():
            raise Conflict(error('Complete your peer mock profile first.', 'onboarding_required'))
        return True


# Base set for every signed-in peer mock endpoint.
PEER_BASE = [IsAuthenticated, FeatureVisibility, IsEmailVerified]
PEER_ONBOARDED = PEER_BASE + [HasPeerProfile]


class _PerUserThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': request.user.pk}


class PeerWriteThrottle(_PerUserThrottle):
    """Writes per user (reads are not counted)."""

    scope = 'peer_write'

    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)


class InviteCodeThrottle(_PerUserThrottle):
    """Onboarding attempts (the only place an invite code is checked)."""

    scope = 'peer_invite'

    def allow_request(self, request, view):
        if request.method != 'PUT' or PeerProfile.objects.filter(user=request.user).exists():
            return True
        return super().allow_request(request, view)


PEER_THROTTLES = [UserRateThrottle, PeerWriteThrottle]
