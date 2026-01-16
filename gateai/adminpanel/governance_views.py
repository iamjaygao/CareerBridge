"""
Adminpanel Governance API Views

REST API endpoints for managing platform governance (SuperAdmin only).

GOVERNANCE POWER CONSTITUTION:
- ALL endpoints require is_superuser=True (not just is_staff)
- Staff (is_staff=True, is_superuser=False) get HTTP 403
- All write operations create GovernanceAudit entries
- All write operations increment PlatformState.governance_version

Endpoints:
- GET /api/v1/adminpanel/governance/platform-state/
- PATCH /api/v1/adminpanel/governance/platform-state/
- GET /api/v1/adminpanel/governance/feature-flags/
- PATCH /api/v1/adminpanel/governance/feature-flags/{key}/
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.shortcuts import get_object_or_404
from kernel.governance.models import PlatformState, FeatureFlag, GovernanceAudit


class IsSuperUser(IsAuthenticated):
    """
    Permission class that only allows superusers.
    
    Staff users (is_staff=True, is_superuser=False) are DENIED.
    """
    
    def has_permission(self, request, view):
        # First check if user is authenticated
        if not super().has_permission(request, view):
            return False
        
        # Then check if user is superuser
        return request.user.is_superuser


class PlatformStateView(APIView):
    """
    GET: Retrieve current platform state
    PATCH: Update platform state (requires reason)
    
    SuperAdmin only.
    """
    
    permission_classes = [IsSuperUser]
    
    def get(self, request):
        """Get current platform state"""
        platform_state = PlatformState.objects.first()
        
        if not platform_state:
            return Response(
                {'detail': 'Platform state not initialized. Run: python manage.py kernel_init_governance'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        data = {
            'id': str(platform_state.id),
            'state': platform_state.state,
            'active_workloads': platform_state.active_workloads,
            'frozen_modules': platform_state.frozen_modules,
            'governance_version': platform_state.governance_version,
            'reason': platform_state.reason,
            'updated_by': platform_state.updated_by.username if platform_state.updated_by else None,
            'updated_at': platform_state.updated_at.isoformat(),
            'created_at': platform_state.created_at.isoformat(),
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update platform state"""
        platform_state = PlatformState.objects.first()
        
        if not platform_state:
            return Response(
                {'detail': 'Platform state not initialized. Run: python manage.py kernel_init_governance'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Require reason for all changes
        reason = request.data.get('reason')
        if not reason:
            raise ValidationError({'reason': 'Reason is required for all governance changes'})
        
        # Store old state for audit
        old_state = {
            'state': platform_state.state,
            'active_workloads': platform_state.active_workloads,
            'frozen_modules': platform_state.frozen_modules,
        }
        
        # Update fields
        if 'state' in request.data:
            platform_state.state = request.data['state']
        
        if 'active_workloads' in request.data:
            platform_state.active_workloads = request.data['active_workloads']
        
        if 'frozen_modules' in request.data:
            platform_state.frozen_modules = request.data['frozen_modules']
        
        platform_state.reason = reason
        platform_state.updated_by = request.user
        platform_state.save()  # This auto-increments governance_version
        
        # Create audit entry (with world context)
        GovernanceAudit.objects.create(
            action='PLATFORM_STATE_UPDATE',
            payload={
                'old_state': old_state,
                'new_state': {
                    'state': platform_state.state,
                    'active_workloads': platform_state.active_workloads,
                    'frozen_modules': platform_state.frozen_modules,
                },
                'governance_version': platform_state.governance_version,
            },
            reason=reason,
            actor=request.user,
            world=getattr(request, 'world', 'kernel')  # Extract from middleware
        )
        
        return Response({
            'detail': 'Platform state updated successfully',
            'governance_version': platform_state.governance_version,
        }, status=status.HTTP_200_OK)


class FeatureFlagListView(APIView):
    """
    GET: List all feature flags
    
    SuperAdmin only.
    """
    
    permission_classes = [IsSuperUser]
    
    def get(self, request):
        """List all feature flags"""
        flags = FeatureFlag.objects.all().order_by('key')
        
        data = [{
            'id': str(flag.id),
            'key': flag.key,
            'state': flag.state,
            'visibility': flag.visibility,
            'rollout_rule': flag.rollout_rule,
            'reason': flag.reason,
            'updated_by': flag.updated_by.username if flag.updated_by else None,
            'updated_at': flag.updated_at.isoformat(),
            'created_at': flag.created_at.isoformat(),
        } for flag in flags]
        
        return Response(data, status=status.HTTP_200_OK)


class FeatureFlagDetailView(APIView):
    """
    GET: Get specific feature flag
    PATCH: Update feature flag (requires reason)
    
    SuperAdmin only.
    """
    
    permission_classes = [IsSuperUser]
    
    def get(self, request, key):
        """Get feature flag by key"""
        flag = get_object_or_404(FeatureFlag, key=key)
        
        data = {
            'id': str(flag.id),
            'key': flag.key,
            'state': flag.state,
            'visibility': flag.visibility,
            'rollout_rule': flag.rollout_rule,
            'reason': flag.reason,
            'updated_by': flag.updated_by.username if flag.updated_by else None,
            'updated_at': flag.updated_at.isoformat(),
            'created_at': flag.created_at.isoformat(),
        }
        
        return Response(data, status=status.HTTP_200_OK)
    
    def patch(self, request, key):
        """Update feature flag"""
        flag = get_object_or_404(FeatureFlag, key=key)
        
        # Require reason for all changes
        reason = request.data.get('reason')
        if not reason:
            raise ValidationError({'reason': 'Reason is required for all governance changes'})
        
        # Store old state for audit
        old_state = {
            'key': flag.key,
            'state': flag.state,
            'visibility': flag.visibility,
            'rollout_rule': flag.rollout_rule,
        }
        
        # Update fields
        if 'state' in request.data:
            if request.data['state'] not in ['OFF', 'BETA', 'ON']:
                raise ValidationError({'state': 'Invalid state. Must be OFF, BETA, or ON'})
            flag.state = request.data['state']
        
        if 'visibility' in request.data:
            if request.data['visibility'] not in ['internal', 'staff', 'user', 'public']:
                raise ValidationError({'visibility': 'Invalid visibility. Must be internal, staff, user, or public'})
            flag.visibility = request.data['visibility']
        
        if 'rollout_rule' in request.data:
            flag.rollout_rule = request.data['rollout_rule']
        
        flag.reason = reason
        flag.updated_by = request.user
        flag.save()
        
        # Increment platform governance version to invalidate middleware cache
        platform_state = PlatformState.objects.first()
        if platform_state:
            platform_state.reason = f'Feature flag {key} updated: {reason}'
            platform_state.updated_by = request.user
            platform_state.save()  # This auto-increments governance_version
        
        # Create audit entry (with world context)
        GovernanceAudit.objects.create(
            action='FEATURE_FLAG_UPDATE',
            payload={
                'old_state': old_state,
                'new_state': {
                    'key': flag.key,
                    'state': flag.state,
                    'visibility': flag.visibility,
                    'rollout_rule': flag.rollout_rule,
                },
                'governance_version': platform_state.governance_version if platform_state else None,
            },
            reason=reason,
            actor=request.user,
            world=getattr(request, 'world', 'kernel')  # Extract from middleware
        )
        
        return Response({
            'detail': f'Feature flag {key} updated successfully',
            'governance_version': platform_state.governance_version if platform_state else None,
        }, status=status.HTTP_200_OK)
