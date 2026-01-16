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
from kernel.governance.models import FeatureFlag, PlatformState
from kernel.worlds import WORLD_NAMESPACES

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
        Update feature flags.
        
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
