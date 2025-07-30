from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.urls import reverse

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
            'mentors': request.build_absolute_uri('/api/v1/mentors/'),
            'appointments': request.build_absolute_uri('/api/v1/appointments/'),
            'resumes': request.build_absolute_uri('/api/v1/resumes/'),
            'payments': request.build_absolute_uri('/api/v1/payments/'),
            'notifications': request.build_absolute_uri('/api/v1/notifications/'),
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