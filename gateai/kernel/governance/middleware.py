"""
Kernel Governance Middleware - 4-World OS Architecture

Enforces bus power and module freezing at the HTTP request level.

This middleware runs before DRF authentication, so it cannot know who the
caller is (JWT users look anonymous here). It therefore applies only
identity-free rules:

1. Bus Power Master Switch: the request's bus must be ON. A path that maps to
   no bus (UNKNOWN) is refused. Refusals return 404.
2. Feature flags in state OFF return 404 for everyone (userland only).

Identity-dependent rules - kernel world is superuser-only, BETA is
superuser-only, flag visibility (user/staff/internal) - are enforced per view
by DRF permission classes (KernelPermission, IsSuperUser,
kernel.governance.permissions.FeatureVisibility).

Flags are read from the DB on every request (no in-process cache), so a flag
change is seen by the next request in every worker.
"""

import logging
from django.http import Http404, HttpResponse
from kernel.worlds import resolve_world, is_kernel_world
from kernel.policies.bus_power import resolve_bus, is_bus_powered, get_bus_state
from kernel.governance.permissions import PATH_TO_FEATURE, resolve_feature_key

logger = logging.getLogger(__name__)


class GovernanceMiddleware:
    """
    Middleware to enforce bus power and frozen (OFF) modules.

    - request.bus and request.world are attached for downstream use.
    - Kernel world is immune to feature flags; access control for it is the
      views' DRF permissions.
    """

    PATH_TO_FEATURE = PATH_TO_FEATURE

    # Paths that are never blocked by feature flags (bus power still applies)
    BYPASS_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/api/schema/',
        '/api/docs/',
        '/swagger/',
        '/redoc/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # STEP 0: Bus Power Master Switch (runs before all other governance)
        bus = resolve_bus(request.path)
        request.bus = bus  # Attach for observability

        if not is_bus_powered(bus):
            logger.info(
                'Bus power OFF - blocking request',
                extra={'path': request.path, 'bus': bus, 'state': get_bus_state(bus)}
            )
            return HttpResponse(status=404)

        # STEP 1: Resolve which world this request belongs to
        request.world = resolve_world(request.path)

        # STEP 2: Userland feature freeze (kernel world is immune)
        if not is_kernel_world(request.world):
            self._check_governance(request)

        return self.get_response(request)

    def _check_governance(self, request):
        """
        Raise Http404 if the path's feature flag is OFF.

        THIS METHOD ONLY RUNS FOR USERLAND (public, app, admin).
        """
        path = request.path

        for bypass_prefix in self.BYPASS_PATHS:
            if path.startswith(bypass_prefix):
                return

        feature_key = self._resolve_feature_key(path)
        if not feature_key:
            return  # Path not governed

        from kernel.governance.models import FeatureFlag, PlatformState

        try:
            governance_ready = PlatformState.objects.exists()
            state = FeatureFlag.objects.filter(key=feature_key).values_list('state', flat=True).first()
        except Exception as e:
            logger.error('Failed to load governance rules', extra={'error': str(e)}, exc_info=True)
            governance_ready, state = False, None

        if not governance_ready:
            # Fail-open for critical modules, fail-closed for others
            if feature_key in ['USERS', 'KERNEL_ADMIN']:
                logger.warning('Governance unavailable - allowing critical path',
                               extra={'path': path, 'feature': feature_key})
                return
            logger.error('Governance unavailable - blocking non-critical path',
                         extra={'path': path, 'feature': feature_key})
            raise Http404('Service temporarily unavailable')

        if state == 'OFF':
            logger.info('Feature disabled - blocking request',
                        extra={'path': path, 'world': request.world, 'feature': feature_key})
            raise Http404('This feature is currently unavailable')

    def _resolve_feature_key(self, path):
        """Resolve path to feature key using prefix matching (None if not governed)."""
        return resolve_feature_key(path)
