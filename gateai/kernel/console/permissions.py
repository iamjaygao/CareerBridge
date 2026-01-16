"""
Kernel Console Permissions

Root-level permission check for kernel console access.
"""

from rest_framework.permissions import BasePermission


class KernelPermission(BasePermission):
    """
    Permission check for kernel console access.
    
    Requirements:
    - User must be authenticated
    - User must be superuser (is_superuser=True)
    - Request must be in kernel world
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser and
            getattr(request, 'world', None) == 'kernel'
        )
