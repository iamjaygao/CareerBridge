from django.urls import path, include
from django.conf import settings
from .views import dispatch_syscall
from .views_observability import audit_stream, lock_snapshot, kernel_pulse, compliance_monitor

urlpatterns = [
    path('dispatch', dispatch_syscall, name='dispatch_syscall'),
    
    # Phase-A.1: Kernel Pulse (Read-only observability plane)
    path('pulse/', include('kernel.pulse.urls')),
    
    # Observability (Sandbox only)
    path('observability/audit', audit_stream, name='audit_stream'),
    path('observability/locks', lock_snapshot, name='lock_snapshot'),
    path('observability/pulse', kernel_pulse, name='kernel_pulse'),
    path('observability/compliance', compliance_monitor, name='compliance_monitor'),
]

if settings.DEBUG:
    from .views_sandbox import atomic_trap
    urlpatterns += [
        path('sandbox/atomic-trap', atomic_trap, name='kernel_atomic_trap'),
    ]
