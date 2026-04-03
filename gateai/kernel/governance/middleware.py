"""
Kernel Governance Middleware - 4-World OS Architecture

Enforces feature flags and module freezing at the HTTP request level.
Now implements a formal 4-world OS model:
- PUBLIC: Marketing, unauthenticated access
- APP: User workloads (students, mentors)
- ADMIN: Userland administration (staff operations)
- KERNEL: OS control plane (superuser only, immune to feature flags)

Features:
- Bus Power Master Switch (Phase-A: 总闸控制)
- World-aware request processing
- Path-to-feature mapping with deterministic routing
- Caching with 5-second TTL to avoid DB queries on every request
- Cache invalidation based on governance_version
- Fail-closed for frozen modules, fail-open for critical paths (users, kernel_admin)
- BETA features visible ONLY to superusers

GOVERNANCE POWER CONSTITUTION:
- OFF features return 404 for everyone (USERLAND ONLY)
- BETA features accessible ONLY to superusers
- ON features accessible based on visibility rules
- KERNEL WORLD is IMMUNE to all feature flags and governance rules

BUS POWER MASTER SWITCH (Phase-A):
- All buses OFF except KERNEL_CORE_BUS
- Bus power check runs BEFORE all other governance
- OFF buses return 404 immediately (no further processing)
- Preparation for future capability activation
"""

import time
import logging
from django.http import Http404, JsonResponse, HttpResponse
from django.core.cache import cache
from django.conf import settings
from kernel.worlds import resolve_world, is_kernel_world, is_userland_world
from kernel.policies.bus_power import resolve_bus, is_bus_powered, get_bus_state
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


class GovernanceMiddleware:
    """
    Middleware to enforce feature flags and module freezing.
    
    Implements 4-World OS Architecture:
    - PUBLIC: Marketing, unauthenticated (feature flags apply)
    - APP: User workloads (feature flags apply)
    - ADMIN: Userland administration (feature flags apply)
    - KERNEL: OS control plane (IMMUNE to feature flags, superuser ONLY)
    
    World Resolution:
    - Each request is classified into one of the 4 worlds
    - request.world attribute is attached for downstream use
    - Kernel world bypasses ALL governance and feature flag checks
    """
    
    # Path prefix to feature key mapping
    PATH_TO_FEATURE = {
        '/peer/': 'PEER_MOCK',
        '/api/v1/users/': 'USERS',
        '/api/v1/adminpanel/': 'KERNEL_ADMIN',
        '/kernel/': 'KERNEL_ADMIN',
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
    
    # Paths that should NEVER be blocked (critical for system operation)
    BYPASS_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/api/schema/',
        '/api/docs/',
        '/swagger/',
        '/redoc/',
    ]
    
    # Cache keys and TTL
    CACHE_KEY_GOVERNANCE_VERSION = 'governance:version'
    CACHE_KEY_FEATURE_FLAGS = 'governance:feature_flags'
    CACHE_TTL = 5  # seconds
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._cached_version = None
        self._cached_flags = None
        self._cache_timestamp = 0
    
    def __call__(self, request):
        # STEP 0: Bus Power Master Switch Check (Phase-A 总闸)
        # This runs BEFORE all other governance checks
        bus = resolve_bus(request.path)
        request.bus = bus  # Attach for observability
        
        if not is_bus_powered(bus):
            # Bus is OFF - return 404 immediately
            logger.info(
                'Bus power OFF - blocking request',
                extra={
                    'path': request.path,
                    'bus': bus,
                    'state': get_bus_state(bus)
                }
            )
            return HttpResponse(status=404)
        
        # Bus is ON - continue to normal governance
        logger.debug(
            'Bus power ON - proceeding',
            extra={'path': request.path, 'bus': bus}
        )
        
        # STEP 1: Kernel world must authenticate JWT manually (middleware runs before DRF)
        if request.path.startswith('/kernel/'):
            try:
                auth = JWTAuthentication()
                user_auth = auth.authenticate(request)
                if user_auth:
                    request.user, _ = user_auth
            except Exception:
                pass
        
        # STEP 2: Resolve which world this request belongs to
        world = resolve_world(request.path)
        request.world = world  # Attach for downstream middleware/views
        
        # STEP 3: Kernel Sovereign Guard
        # Kernel world has absolute priority - check access and bypass all other checks
        if is_kernel_world(world):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated or not user.is_superuser:
                logger.warning(
                    'Kernel access denied - not superuser',
                    extra={'path': request.path, 'world': world, 'user': str(user)}
                )
                return JsonResponse({'detail': 'Kernel access denied'}, status=403)
            
            # Superuser in kernel world - BYPASS ALL governance checks
            logger.debug(
                'Kernel access granted - bypassing all governance',
                extra={'path': request.path, 'world': world, 'user': user.username}
            )
            response = self.get_response(request)
            return response
        
        # STEP 4: Userland governance (public, app, admin)
        # Feature flags and governance rules ONLY apply to userland
        governance_response = self._check_governance(request)
        
        # If governance check returns a response (403/404), return it
        if governance_response is not None:
            return governance_response
        
        # Continue to next middleware/view
        response = self.get_response(request)
        return response
    
    def _check_governance(self, request):
        """
        Check if the requested path is allowed by governance rules.
        
        THIS METHOD ONLY RUNS FOR USERLAND (public, app, admin).
        Kernel world bypasses this entirely.
        
        Raises Http404 if access is denied.
        """
        path = request.path
        world = getattr(request, 'world', 'public')
        
        # Sanity check: This should never run for kernel world
        if is_kernel_world(world):
            logger.error(
                'CRITICAL: Governance check called for kernel world - this should never happen',
                extra={'path': path, 'world': world}
            )
            return  # Allow by default to avoid blocking kernel
        
        # Bypass check for critical paths (Django admin, static files, etc.)
        for bypass_prefix in self.BYPASS_PATHS:
            if path.startswith(bypass_prefix):
                return
        
        # Resolve feature key from path
        feature_key = self._resolve_feature_key(path)
        if not feature_key:
            # Path not governed - allow
            return
        
        # Get feature flag from cache
        feature_flags = self._get_feature_flags()
        
        # Safe defaults if governance unavailable
        if feature_flags is None:
            # Fail-open for critical modules, fail-closed for others
            if feature_key in ['USERS', 'KERNEL_ADMIN']:
                logger.warning(
                    'Governance unavailable - allowing critical path',
                    extra={'path': path, 'feature': feature_key}
                )
                return
            else:
                logger.error(
                    'Governance unavailable - blocking non-critical path',
                    extra={'path': path, 'feature': feature_key}
                )
                raise Http404('Service temporarily unavailable')
        
        # Check if feature is enabled for this user
        flag = feature_flags.get(feature_key)
        if not flag:
            # Feature not found - allow (for backward compatibility)
            logger.warning(
                'Feature flag not found - allowing',
                extra={'path': path, 'feature': feature_key}
            )
            return
        
        # Enforce feature state (USERLAND ONLY)
        if flag['state'] == 'OFF':
            logger.info(
                'Feature disabled - blocking request',
                extra={'path': path, 'world': world, 'feature': feature_key}
            )
            raise Http404('This feature is currently unavailable')
        
        if flag['state'] == 'BETA':
            # BETA features only for superusers (GOVERNANCE POWER CONSTITUTION)
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated or not user.is_superuser:
                logger.info(
                    'Beta feature access denied - not superuser',
                    extra={'path': path, 'world': world, 'feature': feature_key, 'user': user}
                )
                raise Http404('This feature is in beta testing')
        
        if flag['state'] == 'ON':
            # Check visibility rules
            user = getattr(request, 'user', None)
            if not self._check_visibility(flag['visibility'], user):
                logger.info(
                    'Feature visibility check failed',
                    extra={'path': path, 'world': world, 'feature': feature_key, 'visibility': flag['visibility']}
                )
                raise Http404('You do not have access to this feature')
        
        # Access allowed
        return
    
    def _resolve_feature_key(self, path):
        """
        Resolve path to feature key using prefix matching.
        
        Returns feature key or None if path is not governed.
        """
        for prefix, feature_key in self.PATH_TO_FEATURE.items():
            if path.startswith(prefix):
                return feature_key
        return None
    
    def _check_visibility(self, visibility, user):
        """Check if user meets visibility requirements"""
        if visibility == 'public':
            return True
        if visibility == 'user' and user and user.is_authenticated:
            return True
        if visibility == 'staff' and user and user.is_staff:
            return True
        if visibility == 'internal' and user and user.is_superuser:
            return True
        return False
    
    def _get_feature_flags(self):
        """
        Get feature flags from cache or DB.
        
        Uses in-process cache with 5-second TTL and version-based invalidation.
        
        Returns:
            dict: Feature key -> {state, visibility, rollout_rule}
            None: If governance is unavailable
        """
        now = time.time()
        
        # Check if in-process cache is still valid
        if self._cached_flags and (now - self._cache_timestamp) < self.CACHE_TTL:
            # Check if governance version has changed
            current_version = self._get_governance_version()
            if current_version and current_version == self._cached_version:
                return self._cached_flags
        
        # Cache miss or expired - fetch from DB
        try:
            from kernel.governance.models import FeatureFlag, PlatformState
            
            # Get current governance version
            platform_state = PlatformState.objects.first()
            if not platform_state:
                logger.warning('PlatformState not initialized')
                return None
            
            current_version = platform_state.governance_version
            
            # Fetch all feature flags
            flags = FeatureFlag.objects.all().values('key', 'state', 'visibility', 'rollout_rule')
            feature_flags = {
                flag['key']: {
                    'state': flag['state'],
                    'visibility': flag['visibility'],
                    'rollout_rule': flag['rollout_rule'],
                }
                for flag in flags
            }
            
            # Update in-process cache
            self._cached_flags = feature_flags
            self._cached_version = current_version
            self._cache_timestamp = now
            
            # Also update Django cache for other processes
            cache.set(self.CACHE_KEY_FEATURE_FLAGS, feature_flags, self.CACHE_TTL)
            cache.set(self.CACHE_KEY_GOVERNANCE_VERSION, current_version, self.CACHE_TTL)
            
            return feature_flags
            
        except Exception as e:
            logger.error(
                'Failed to load governance rules',
                extra={'error': str(e)},
                exc_info=True
            )
            return None
    
    def _get_governance_version(self):
        """Get current governance version from cache"""
        try:
            return cache.get(self.CACHE_KEY_GOVERNANCE_VERSION)
        except Exception:
            return None
