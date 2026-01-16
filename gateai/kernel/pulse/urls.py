"""
Kernel Pulse URL Configuration
"""

from django.urls import path
from .views import KernelPulseSummaryView

urlpatterns = [
    path('summary/', KernelPulseSummaryView.as_view(), name='kernel_pulse_summary'),
]
