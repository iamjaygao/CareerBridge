"""
Kernel Console URL Configuration

Root shell endpoints for kernel control plane.
"""

from django.urls import path
from .views import (
    KernelStatusView,
    KernelFeatureFlagsView,
    KernelWorldMapView,
    KernelUserListView,
)

urlpatterns = [
    path('status/', KernelStatusView.as_view(), name='kernel_console_status'),
    path('flags/', KernelFeatureFlagsView.as_view(), name='kernel_console_flags'),
    path('world-map/', KernelWorldMapView.as_view(), name='kernel_console_world_map'),
    path('users/', KernelUserListView.as_view(), name='kernel_console_users'),
]
