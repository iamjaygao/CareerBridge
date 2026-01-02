"""
Placeholder URL configuration for Job Ingestion Engine namespace.

RESERVED NAMESPACE: /api/engines/job-ingestion/

This namespace is reserved for future Job Ingestion Engine integration.
This engine slot is not currently implemented.

Status: Reserved - Not Available
See docs/GATEAI_OS_CONTRACT.md for details.
"""

from django.urls import path
from django.http import JsonResponse, HttpResponseNotFound


def placeholder_view(request):
    """Placeholder view for reserved engine namespace."""
    return JsonResponse({
        'error': 'Not Implemented',
        'message': 'This engine namespace is reserved but not yet implemented.',
        'namespace': '/api/engines/job-ingestion/',
        'status': 'reserved',
        'documentation': '/docs/GATEAI_OS_CONTRACT.md',
    }, status=404)


urlpatterns = [
    # Placeholder - all paths return 404
    path('', placeholder_view, name='job-ingestion-placeholder'),
]

