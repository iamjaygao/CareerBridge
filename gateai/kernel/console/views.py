"""
Kernel Console Views

Root shell endpoints for GateAI OS kernel control plane.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

from kernel.console.permissions import KernelPermission
from kernel.governance.models import FeatureFlag, PlatformState, BusPowerState, GovernanceAudit
from kernel.worlds import WORLD_NAMESPACES
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

User = get_user_model()


class KernelStatusView(APIView):
    """
    GET /kernel/console/status/
    
    Returns the current kernel and platform state.
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [KernelPermission]

    def get(self, request):
        ps = PlatformState.objects.first()
        return Response({
            "governance_version": ps.governance_version if ps else None,
            "platform_state": ps.state if ps else None,
            "active_workloads": ps.active_workloads if ps else [],
            "frozen_modules": ps.frozen_modules if ps else [],
            "kernel_online": True,
            "world": getattr(request, 'world', None),
        })


class KernelFeatureFlagsView(APIView):
    """
    GET /kernel/console/flags/
    POST /kernel/console/flags/
    
    View and update feature flags from kernel console.
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [KernelPermission]

    def get(self, request):
        """List all feature flags"""
        flags = FeatureFlag.objects.all().values(
            'id', 'key', 'state', 'visibility', 
            'rollout_rule', 'reason', 'updated_at'
        )
        return Response(list(flags))

    def post(self, request):
        """
        Update feature flags (backward-compat string format).

        Payload format:
        {
            "FLAG_KEY": "ON|OFF|BETA",
            "ANOTHER_FLAG": "OFF"
        }
        """
        for key, state in request.data.items():
            if state not in ['ON', 'OFF', 'BETA']:
                continue
            FeatureFlag.objects.filter(key=key).update(
                state=state,
                updated_by=request.user
            )
        return Response({"status": "updated"})

    def patch(self, request):
        """
        Update feature flags with state + visibility.

        Payload format:
        {
            "ATS_SIGNALS": { "state": "ON", "visibility": "user" },
            "ANOTHER_FLAG": { "state": "OFF", "visibility": "internal" }
        }
        """
        VALID_STATES = {'ON', 'OFF', 'BETA'}
        VALID_VISIBILITIES = {'public', 'user', 'staff', 'internal'}

        updated = []
        errors = []

        for key, value in request.data.items():
            if not isinstance(value, dict):
                errors.append(f"{key}: value must be an object with 'state' and/or 'visibility'")
                continue

            new_state = value.get('state')
            new_visibility = value.get('visibility')

            if new_state is not None and new_state not in VALID_STATES:
                errors.append(f"{key}: invalid state '{new_state}' (must be ON, OFF, or BETA)")
                continue

            if new_visibility is not None and new_visibility not in VALID_VISIBILITIES:
                errors.append(f"{key}: invalid visibility '{new_visibility}' (must be public, user, staff, or internal)")
                continue

            qs = FeatureFlag.objects.filter(key=key)
            flag = qs.first()
            if not flag:
                errors.append(f"{key}: feature flag not found")
                continue

            old_state = flag.state
            old_visibility = flag.visibility

            update_fields = {'updated_by': request.user}
            if new_state is not None:
                update_fields['state'] = new_state
            if new_visibility is not None:
                update_fields['visibility'] = new_visibility

            qs.update(**update_fields)

            action = 'MODULE_ENABLE' if (new_state or old_state) == 'ON' else 'MODULE_DISABLE'
            if new_state == 'ON':
                action = 'MODULE_ENABLE'
            elif new_state in ('OFF', 'BETA'):
                action = 'MODULE_DISABLE'

            GovernanceAudit.objects.create(
                action=action,
                payload={
                    'key': key,
                    'old_state': old_state,
                    'new_state': new_state or old_state,
                    'visibility': new_visibility or old_visibility,
                },
                reason=f"Feature flag updated via kernel console by {request.user.username}",
                actor=request.user,
                world='kernel',
            )

            updated.append({
                'key': key,
                'state': new_state or old_state,
                'visibility': new_visibility or old_visibility,
            })

        return Response({'updated': updated, 'errors': errors})


class KernelWorldMapView(APIView):
    """
    GET /kernel/console/world-map/
    
    Returns the 4-World OS namespace map.
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [KernelPermission]

    def get(self, request):
        return Response({
            "worlds": WORLD_NAMESPACES,
            "current_world": getattr(request, 'world', None),
        })


class KernelUserListView(APIView):
    """
    GET /kernel/console/users/

    Returns list of superuser accounts.
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [KernelPermission]

    def get(self, request):
        superusers = User.objects.filter(is_superuser=True).values(
            "id", "username", "email", "is_active", "date_joined"
        )
        return Response(list(superusers))


class KernelBusPowerView(APIView):
    """
    GET  /kernel/console/buses/       — list all bus power states
    PATCH /kernel/console/buses/      — update one or more buses (superadmin only)

    PATCH payload:
        { "AI_BUS": "ON", "MENTOR_BUS": "OFF" }

    Only superadmin (is_superuser=True) can reach this endpoint because it lives
    under /kernel/ which is protected by KernelPermission + GovernanceMiddleware.
    """
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [KernelPermission]

    def get(self, request):
        buses = BusPowerState.objects.all().values(
            "bus_name", "state", "reason", "updated_at"
        )
        # If DB is empty (first boot before seed), return defaults
        if not buses:
            return Response([
                {"bus_name": k, "state": v, "reason": "", "updated_at": None}
                for k, v in BUS_POWER_DEFAULTS.items()
            ])
        return Response(list(buses))

    def patch(self, request):
        updated = []
        errors = []

        for bus_name, new_state in request.data.items():
            if new_state not in ("ON", "OFF"):
                errors.append(f"{bus_name}: invalid state '{new_state}' (must be ON or OFF)")
                continue

            if bus_name == "KERNEL_CORE_BUS":
                errors.append("KERNEL_CORE_BUS cannot be turned off")
                continue

            if bus_name not in BUS_POWER_DEFAULTS:
                errors.append(f"{bus_name}: unknown bus")
                continue

            obj, created = BusPowerState.objects.get_or_create(
                bus_name=bus_name,
                defaults={"state": new_state, "updated_by": request.user},
            )
            if not created:
                old_state = obj.state
                obj.state = new_state
                obj.updated_by = request.user
                obj.save()
            else:
                old_state = BUS_POWER_DEFAULTS.get(bus_name, "OFF")

            # Write audit log
            GovernanceAudit.objects.create(
                action="MODULE_ENABLE" if new_state == "ON" else "MODULE_DISABLE",
                payload={"bus": bus_name, "old_state": old_state, "new_state": new_state},
                reason=f"Bus power changed via kernel console by {request.user.username}",
                actor=request.user,
                world="kernel",
            )
            updated.append({"bus_name": bus_name, "state": new_state})

        # Invalidate in-process cache so next request picks up new values
        invalidate_cache()

        return Response({
            "updated": updated,
            "errors": errors,
        })
