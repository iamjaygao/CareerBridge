"""
Prometheus metrics endpoint for the scraper.

Disabled (404) unless METRICS_TOKEN is set; requires
`Authorization: Bearer <METRICS_TOKEN>`. nginx does not route /metrics/, so
only Prometheus on the internal network can reach it.
"""

import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django_prometheus.exports import ExportToDjangoView


def metrics_view(request):
    token = getattr(settings, 'METRICS_TOKEN', '')
    if not token:
        return HttpResponseNotFound()
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        response = HttpResponse(status=401)
        response['WWW-Authenticate'] = 'Bearer'
        return response
    if not hmac.compare_digest(header[len('Bearer '):].encode(), token.encode()):
        return HttpResponse(status=403)
    return ExportToDjangoView(request)
