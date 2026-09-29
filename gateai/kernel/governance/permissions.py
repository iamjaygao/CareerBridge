"""
Identity-dependent governance checks, enforced by DRF.

GovernanceMiddleware runs before DRF authentication, so it cannot see JWT
users. It therefore only applies identity-free rules (bus power, flag OFF).
Everything that depends on who the caller is lives here, evaluated after DRF
has authenticated the request:

- BETA features: superusers only.
- ON features, by visibility:
    public / user -> no extra restriction (the view's own permission decides,
                     e.g. AllowAny for signup, IsAuthenticated for profile)
    staff         -> is_staff
    internal      -> is_superuser
- OFF features: hidden (the middleware already returns 404; repeated here as
  defence in depth).

Denials raise 404 rather than 403 so hidden features stay hidden.
"""

from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission

# Path prefix -> feature key. First match wins, so list longer prefixes first.
PATH_TO_FEATURE = {
    '/peer/': 'PEER_MOCK',
    '/api/v1/peer-mock/': 'PEER_MOCK',
    '/api/v1/users/': 'USERS',
    '/api/v1/adminpanel/': 'KERNEL_ADMIN',
    '/api/v1/kernel/': 'KERNEL_ADMIN',
    '/api/v1/decision-slots/': 'DECISION_SLOTS',
    '/api/v1/human-loop/': 'HUMAN_LOOP',

    # Frozen modules (Phase-A)
    '/api/v1/appointments/': 'APPOINTMENTS',
    '/api/v1/payments/': 'PAYMENTS',
    '/api/v1/chat/': 'CHAT',
    '/api/v1/search/': 'SEARCH',
    '/api/v1/signal-delivery/': 'SIGNAL_DELIVERY',
    '/api/v1/ats-signals/': 'ATS_SIGNALS',
    '/api/engines/signal-core/': 'ENGINES_SIGNAL_CORE',
    '/api/engines/job-ingestion/': 'ENGINES_JOB_INGESTION',
}


def resolve_feature_key(path):
    for prefix, feature_key in PATH_TO_FEATURE.items():
        if path.startswith(prefix):
            return feature_key
    return None


def _visible_to(visibility, user):
    if visibility in ('public', 'user'):
        return True
    if visibility == 'staff':
        return bool(user and user.is_staff)
    if visibility == 'internal':
        return bool(user and user.is_superuser)
    return False


class FeatureVisibility(BasePermission):
    """Apply the governing feature flag's BETA/visibility rule to the DRF user."""

    def has_permission(self, request, view):
        from kernel.governance.models import FeatureFlag

        feature_key = resolve_feature_key(request.path)
        if not feature_key:
            return True

        flag = FeatureFlag.objects.filter(key=feature_key).values('state', 'visibility').first()
        if flag is None:
            return True  # ungoverned feature (same as the middleware)

        user = request.user if request.user and request.user.is_authenticated else None
        if flag['state'] == 'OFF':
            raise NotFound('This feature is currently unavailable')
        if flag['state'] == 'BETA':
            if not (user and user.is_superuser):
                raise NotFound('This feature is in beta testing')
            return True
        if not _visible_to(flag['visibility'], user):
            raise NotFound('You do not have access to this feature')
        return True
