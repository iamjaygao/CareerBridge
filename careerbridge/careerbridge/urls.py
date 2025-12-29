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
        path('api/v1/mentors/', include('mentors.urls')),
        path('api/v1/appointments/', include('appointments.urls')),
        path('api/v1/notifications/', include('notifications.urls')),
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
    path('api/v1/mentors/', include('mentors.urls')), # Mentor profile / availability / reviews
    path('api/v1/appointments/', include('appointments.urls')), # Appointment booking / cancellation
    path('api/v1/adminpanel/', include('adminpanel.urls')), # Admin panel for managing users, mentors, appointments, etc.
    path('api/v1/notifications/', include('notifications.urls')), # Notifications for users
    path('api/v1/resumes/', include('resumes.urls')), # Resume management
    path('api/v1/payments/', include('payments.urls')), # Payment management
    path('api/v1/chat/', include('chat.urls')), # Real-time chat
    path('api/v1/search/', include('search.urls')), # Search functionality

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





