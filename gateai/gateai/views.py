"""
CareerBridge main views
"""

from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.urls import reverse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import structlog

logger = structlog.get_logger()

def home(request):
    """Homepage view"""
    return render(request, 'home.html', {
        'title': 'CareerBridge - Connect with Career Mentors',
        'description': 'Find and connect with experienced career mentors to advance your professional journey.'
    })

@api_view(['GET'])
def api_root(request):
    """API root endpoint showing available endpoints"""
    return Response({
        'message': 'Welcome to CareerBridge API',
        'version': 'v1',
        'endpoints': {
            'users': request.build_absolute_uri('/api/v1/users/'),
            'mentors': request.build_absolute_uri('/api/v1/human-loop/'),  # Legacy name, redirects to new path
            'human_loop': request.build_absolute_uri('/api/v1/human-loop/'),
            'appointments': request.build_absolute_uri('/api/v1/decision-slots/'),  # Legacy name, redirects to new path
            'decision_slots': request.build_absolute_uri('/api/v1/decision-slots/'),
            'resumes': request.build_absolute_uri('/api/v1/ats-signals/'),  # Legacy name, redirects to new path
            'ats_signals': request.build_absolute_uri('/api/v1/ats-signals/'),
            'payments': request.build_absolute_uri('/api/v1/payments/'),
            'notifications': request.build_absolute_uri('/api/v1/signal-delivery/'),  # Legacy name, redirects to new path
            'signal_delivery': request.build_absolute_uri('/api/v1/signal-delivery/'),
            'admin_panel': request.build_absolute_uri('/api/v1/adminpanel/'),
        },
        'documentation': {
            'swagger': request.build_absolute_uri('/swagger/'),
            'redoc': request.build_absolute_uri('/redoc/'),
        },
        'authentication': {
            'login': request.build_absolute_uri('/api/v1/users/login/'),
            'register': request.build_absolute_uri('/api/v1/users/register/'),
        }
    })

def health_check(request):
    """Health check endpoint for the application"""
    health_status = {
        "status": "healthy",
        "service": "CareerBridge",
        "version": "1.0.0",
        "components": {}
    }

    # Check database
    try:
        connection.ensure_connection()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Check cache
    try:
        cache.set("health_check", "ok", 10)
        cache_value = cache.get("health_check")
        if cache_value == "ok":
            health_status["components"]["cache"] = "healthy"
        else:
            health_status["components"]["cache"] = "unhealthy"
            health_status["status"] = "unhealthy"
    except Exception as e:
        logger.error("Cache health check failed", error=str(e))
        health_status["components"]["cache"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Check external services (restricted to staff or debug)
    include_external = getattr(settings, 'DEBUG', False)
    if not include_external:
        user = getattr(request, 'user', None)
        include_external = bool(user and user.is_authenticated and user.is_staff)

    if include_external:
        try:
            # Check JobCrawler health
            from careerbridge.external_services.third_party_apis.job_crawler import job_crawler_service
            job_crawler_health = job_crawler_service.check_health()
            
            # Check ResumeMatcher health
            from careerbridge.external_services.third_party_apis.resume_matcher import resume_matcher_service
            resume_matcher_health = resume_matcher_service.check_health()
            
            external_health = {
                'job_crawler': {
                    'status': job_crawler_health.get('status', 'unknown'),
                    'error': job_crawler_health.get('error', None)
                },
                'resume_matcher': {
                    'status': resume_matcher_health.get('status', 'unknown'),
                    'error': resume_matcher_health.get('error', None)
                },
                'ai_analyzer': {
                    'status': 'not_implemented',
                    'error': 'AI Analyzer service not yet implemented'
                }
            }
            health_status["components"]["external_services"] = external_health
        except Exception as e:
            logger.error("External services health check failed", error=str(e))
            health_status["components"]["external_services"] = "unhealthy"
            health_status["status"] = "unhealthy"
    else:
        health_status["components"]["external_services"] = "restricted"

    return JsonResponse(health_status)

@api_view(['GET'])
def ping_endpoint(request):
    """Ping endpoint for measuring API latency - used by unified health check"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat()
    })

def api_info(request):
    """API information endpoint"""
    return JsonResponse({
        "name": "CareerBridge API",
        "version": "1.0.0",
        "description": "AI-powered career development platform",
        "endpoints": {
            "health": "/health/",
            "api_docs": "/api/docs/",
            "admin": "/admin/",
            "resumes": "/api/ats-signals/",  # Legacy endpoint, redirects to new path
            "ats_signals": "/api/ats-signals/",
            "mentors": "/api/human-loop/",  # Legacy endpoint, redirects to new path
            "human_loop": "/api/human-loop/",
            "appointments": "/api/decision-slots/",  # Legacy endpoint, redirects to new path
            "decision_slots": "/api/decision-slots/",
            "payments": "/api/payments/"
        }
    }) 
