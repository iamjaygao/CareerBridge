"""
Access control shared by kernel API views (all under /api/v1/kernel/).

Kernel endpoints are superuser-only. Authentication is JWT (the SPA) or
session (the server-rendered pulse page); DRF answers anonymous callers
with 401 and authenticated non-superusers with 403.
"""

from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from kernel.console.permissions import KernelPermission
from kernel.governance.permissions import FeatureVisibility

KERNEL_AUTHENTICATION = [JWTAuthentication, SessionAuthentication]
KERNEL_PERMISSIONS = [KernelPermission, FeatureVisibility]


def kernel_api_view(methods):
    """Turn a plain function view into a superuser-only DRF view."""
    def decorate(func):
        func = permission_classes(KERNEL_PERMISSIONS)(func)
        func = authentication_classes(KERNEL_AUTHENTICATION)(func)
        return api_view(methods)(func)
    return decorate
