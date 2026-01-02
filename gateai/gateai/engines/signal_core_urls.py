"""
Signal Core Engine URL configuration.

RESERVED NAMESPACE: /api/engines/signal-core/

This namespace exposes Signal Core Engine implementations.
Currently implements: ResumeAuditEngine

See docs/GATEAI_OS_CONTRACT.md for details.
"""

from django.urls import path
from django.http import JsonResponse

from .signal_core_views import resume_audit_view


def placeholder_view(request):
    """Placeholder view for reserved engine namespace (for unimplemented endpoints)."""
    return JsonResponse({
        'error': 'Not Implemented',
        'message': 'This engine endpoint is reserved but not yet implemented.',
        'namespace': '/api/engines/signal-core/',
        'status': 'reserved',
        'documentation': '/docs/GATEAI_OS_CONTRACT.md',
        'available_endpoints': [
            '/api/engines/signal-core/resume-audit/',
        ],
    }, status=404)


urlpatterns = [
    # Resume Audit Engine endpoint
    path('resume-audit/', resume_audit_view, name='signal-core-resume-audit'),
    
    # Root placeholder (for other unimplemented endpoints)
    path('', placeholder_view, name='signal-core-placeholder'),
]

