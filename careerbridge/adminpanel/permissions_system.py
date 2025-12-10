"""
System-level permissions - ONLY for superadmin
These permissions control access to system configuration, logs, and critical operations.
"""
from rest_framework import permissions
from .permissions import is_superadmin


class IsSuperAdminOnly(permissions.BasePermission):
    """
    Permission class: ONLY superadmin can access.
    Admin cannot access system-level features.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Only superadmin
        return is_superadmin(request.user)


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class: Superadmin has full access, others read-only.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superadmin has full access
        if is_superadmin(request.user):
            return True
        
        # Others can only read
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False

