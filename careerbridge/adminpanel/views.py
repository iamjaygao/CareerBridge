from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from .models import (
    SystemStats, AdminAction, SystemConfig, DataExport, ContentModeration
)
from .serializers import (
    SystemStatsSerializer, AdminActionSerializer, SystemConfigSerializer,
    SystemConfigUpdateSerializer, DataExportSerializer, DataExportCreateSerializer,
    ContentModerationSerializer, ContentModerationUpdateSerializer,
    DashboardStatsSerializer, UserManagementSerializer, MentorManagementSerializer,
    AppointmentManagementSerializer, SystemHealthSerializer
)

User = get_user_model()

class AdminDashboardView(generics.GenericAPIView):
    """Admin dashboard"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get dashboard statistics"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        active_users_today = User.objects.filter(last_login__date=today).count()
        new_users_today = User.objects.filter(date_joined__date=today).count()
        
        # Mentor statistics
        from mentors.models import MentorProfile, MentorApplication
        total_mentors = MentorProfile.objects.count()
        active_mentors = MentorProfile.objects.filter(status='active').count()
        pending_applications = MentorApplication.objects.filter(status='pending').count()
        
        # Appointment statistics
        from appointments.models import Appointment
        total_appointments = Appointment.objects.count()
        appointments_today = Appointment.objects.filter(scheduled_start__date=today).count()
        completed_today = Appointment.objects.filter(
            status='completed',
            actual_end__date=today
        ).count()
        
        # Revenue statistics (needs to be adjusted based on actual payment model)
        total_revenue = 0  # Need to get from payment model
        revenue_today = 0  # Need to get from payment model
        
        # System performance (needs actual monitoring data)
        avg_response_time = 0
        error_rate = 0
        uptime_percentage = 100
        
        data = {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'new_users_today': new_users_today,
            'total_mentors': total_mentors,
            'active_mentors': active_mentors,
            'pending_applications': pending_applications,
            'total_appointments': total_appointments,
            'appointments_today': appointments_today,
            'completed_today': completed_today,
            'total_revenue': total_revenue,
            'revenue_today': revenue_today,
            'avg_response_time': avg_response_time,
            'error_rate': error_rate,
            'uptime_percentage': uptime_percentage,
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)

class SystemStatsListView(generics.ListAPIView):
    """System statistics list"""
    serializer_class = SystemStatsSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SystemStats.objects.all()

class SystemStatsDetailView(generics.RetrieveAPIView):
    """System statistics details"""
    serializer_class = SystemStatsSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SystemStats.objects.all()

class AdminActionListView(generics.ListAPIView):
    """Admin action log list"""
    serializer_class = AdminActionSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = AdminAction.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by admin user
        admin_user = self.request.query_params.get('admin_user')
        if admin_user:
            queryset = queryset.filter(admin_user__username__icontains=admin_user)
        
        # Filter by date
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset

class SystemConfigListView(generics.ListCreateAPIView):
    """System configuration list"""
    serializer_class = SystemConfigSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SystemConfig.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by configuration type
        config_type = self.request.query_params.get('config_type')
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset

class SystemConfigDetailView(generics.RetrieveUpdateDestroyAPIView):
    """System configuration details"""
    serializer_class = SystemConfigUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SystemConfig.objects.all()

class DataExportListView(generics.ListCreateAPIView):
    """Data export list"""
    serializer_class = DataExportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DataExportCreateSerializer
        return DataExportSerializer
    
    def get_queryset(self):
        return DataExport.objects.filter(requested_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save()

class DataExportDetailView(generics.RetrieveAPIView):
    """Data export details"""
    serializer_class = DataExportSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = DataExport.objects.all()

class ContentModerationListView(generics.ListAPIView):
    """Content moderation list"""
    serializer_class = ContentModerationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ContentModeration.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

class ContentModerationDetailView(generics.RetrieveUpdateAPIView):
    """Content moderation details"""
    serializer_class = ContentModerationUpdateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ContentModeration.objects.all()

class UserManagementView(generics.GenericAPIView):
    """User management"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get user list"""
        users = User.objects.annotate(
            total_appointments=Count('appointments'),
            total_resumes=Count('resumes')
        ).values(
            'id', 'username', 'email', 'is_active', 'is_staff',
            'date_joined', 'last_login', 'total_appointments', 'total_resumes'
        )
        
        serializer = UserManagementSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Update user status"""
        user_id = request.data.get('user_id')
        action = request.data.get('action')  # 'activate', 'deactivate', 'make_staff'
        
        try:
            user = User.objects.get(id=user_id)
            
            if action == 'activate':
                user.is_active = True
            elif action == 'deactivate':
                user.is_active = False
            elif action == 'make_staff':
                user.is_staff = True
            elif action == 'remove_staff':
                user.is_staff = False
            
            user.save()
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='user_management',
                action_description=f'{action} user {user.username}',
                target_model='User',
                target_id=user.id,
                action_data={'action': action},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'User {action} successfully'})
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class MentorManagementView(generics.GenericAPIView):
    """Mentor management"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get mentor list"""
        from mentors.models import MentorProfile
        
        mentors = MentorProfile.objects.select_related('user').annotate(
            total_sessions=Count('appointments'),
            average_rating=Sum('appointments__user_rating') / Count('appointments')
        ).values(
            'id', 'user__id', 'user__username', 'user__email', 'status',
            'is_approved', 'total_sessions', 'average_rating', 'total_earnings'
        )
        
        serializer = MentorManagementSerializer(mentors, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Update mentor status"""
        mentor_id = request.data.get('mentor_id')
        action = request.data.get('action')  # 'approve', 'reject', 'suspend'
        
        try:
            from mentors.models import MentorProfile
            mentor = MentorProfile.objects.get(id=mentor_id)
            
            if action == 'approve':
                mentor.is_approved = True
                mentor.status = 'active'
            elif action == 'reject':
                mentor.is_approved = False
                mentor.status = 'rejected'
            elif action == 'suspend':
                mentor.status = 'suspended'
            
            mentor.save()
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='mentor_management',
                action_description=f'{action} mentor {mentor.user.username}',
                target_model='MentorProfile',
                target_id=mentor.id,
                action_data={'action': action},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'Mentor {action} successfully'})
        
        except MentorProfile.DoesNotExist:
            return Response(
                {'error': 'Mentor not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class SystemHealthView(generics.GenericAPIView):
    """System health status"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get system health status"""
        # Actual system monitoring data is needed here
        data = {
            'database_status': 'healthy',
            'cache_status': 'healthy',
            'external_services_status': {
                'email_service': 'healthy',
                'payment_service': 'healthy',
                'ai_service': 'healthy'
            },
            'disk_usage': 45.2,
            'memory_usage': 67.8,
            'cpu_usage': 23.1,
            'active_connections': 15,
            'error_count_last_hour': 0
        }
        
        serializer = SystemHealthSerializer(data)
        return Response(serializer.data)
