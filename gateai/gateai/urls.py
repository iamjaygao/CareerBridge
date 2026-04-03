"""
URL configuration for careerbridge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from . import views
from .external_services.health_check import health_checker
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings

#swagger UI setup for drf-yasg  
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from django.conf import settings    
from django.conf.urls.static import static

# swagger documentation information
schema_permission_classes = (permissions.AllowAny,) if settings.DEBUG else (permissions.IsAdminUser,)
schema_view = get_schema_view(
    openapi.Info(
        title="CareerBridge API",
        default_version='v1',
        description="API documentation for CareerBridge",
        contact=openapi.Contact(email="contact@careerbridge.com"),
    ),
    public=settings.DEBUG,
    permission_classes=schema_permission_classes,
    patterns=[
        path('api/v1/users/', include('users.urls')),
        path('api/v1/appointments/', include('appointments.urls')),
        path('api/v1/decision-slots/', include('decision_slots.urls')),
        path('api/v1/signal-delivery/', include('signal_delivery.urls')),
        path('api/v1/adminpanel/', include('adminpanel.urls')),
    ],
)
urlpatterns = [
    # homepage
    path('', views.home, name='home'),
    
    # Health check
    path('health/', views.health_check, name='health-check'),
    path('api/v1/ping/', views.ping_endpoint, name='ping-endpoint'),  # Unified ping endpoint
    path('api/info/', views.api_info, name='api-info'),
    
    # API root
    path('api/v1/', views.api_root, name='api-root'),
    
    # admin panel 
    path('admin/', admin.site.urls),

    # api endpoints from each app
    path('api/v1/users/', include('users.urls')), # Register / login 
    path('api/v1/human-loop/', include('human_loop.urls')), # Human-in-the-loop Layer (formerly Mentor profile / availability / reviews)
    
    # Backward compatibility redirect
    path('api/v1/mentors/', RedirectView.as_view(url='/api/v1/human-loop/', permanent=False)),
    
    # Appointment domain (isolated from kernel)
    path('api/v1/appointments/', include('appointments.urls')),
    
    # Decision Slot System (kernel arbitration only)
    path('api/v1/decision-slots/', include('decision_slots.urls')),
    path('api/v1/adminpanel/', include('adminpanel.urls')), # Admin panel for managing users, mentors, appointments, etc.
    path('api/v1/signal-delivery/', include('signal_delivery.urls')), # Signal Delivery Layer (formerly Notifications for users)
    
    # Backward compatibility redirect
    path('api/v1/notifications/', RedirectView.as_view(url='/api/v1/signal-delivery/', permanent=False)),
    path('api/v1/ats-signals/', include('ats_signals.urls')), # ATS Signal Engine (formerly Resume management)
    
    # Backward compatibility redirect
    path('api/v1/resumes/', RedirectView.as_view(url='/api/v1/ats-signals/', permanent=False)),
    path('api/v1/payments/', include('payments.urls')), # Payment management
    path('api/v1/chat/', include('chat.urls')), # Real-time chat
    path('api/v1/search/', include('search.urls')), # Search functionality
    
    # Phase-B: Peer Mock Runtime (experimental capability)
    path('api/v1/peer-mock/', include('peer_mock.urls')),

    # GateAI Kernel API (Phase-A: Kernel Control Plane)
    path('api/v1/kernel/', include('kernel.urls')),

    # GateAI Kernel Console — API path (apiClient uses /api/v1 baseURL)
    path('api/v1/kernel/console/', include('kernel.console.urls')),

    # GateAI Kernel Syscalls (legacy direct path)
    path('kernel/', include('kernel.urls')),

    # GateAI Kernel Console (Root Control Plane)
    path('kernel/console/', include('kernel.console.urls')),

    # Reserved engine namespaces (not yet implemented)
    # See docs/GATEAI_OS_CONTRACT.md for details
    path('api/engines/signal-core/', include('gateai.engines.signal_core_urls')), # Reserved: Signal Core Engine
    path('api/engines/job-ingestion/', include('gateai.engines.job_ingestion_urls')), # Reserved: Job Ingestion Engine

    # service metrics (admin-only, debug-only)
    path('api/v1/services/metrics/',
         (lambda request: (
             HttpResponseNotFound() if not getattr(settings, 'DEBUG', False)
             else (JsonResponse(__import__('careerbridge.external_services.utils', fromlist=['get_service_metrics']).get_service_metrics())
                   if (request.user.is_authenticated and request.user.is_staff)
                   else HttpResponseForbidden())
         )),
         name='service-metrics'),

    # swagger documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


]

# swagger / redoc documentation - only exosed if DEBUG is True
if settings.DEBUG:
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)





