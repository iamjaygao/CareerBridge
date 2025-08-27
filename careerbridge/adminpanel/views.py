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
            'id', 'username', 'email', 'is_active', 'is_staff', 'role',
            'date_joined', 'last_login', 'total_appointments', 'total_resumes'
        )
        
        # Transform the data to match the serializer expectations
        transformed_users = []
        for user in users:
            transformed_users.append({
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'is_active': user['is_active'],
                'is_staff': user['is_staff'],
                'role': user['role'],
                'date_joined': user['date_joined'],
                'last_login': user['last_login'],
                'total_appointments': user['total_appointments'],
                'total_resumes': user['total_resumes']
            })
        
        serializer = UserManagementSerializer(transformed_users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Handle user management actions"""
        action = request.data.get('action')
        
        if action == 'create':
            return self.create_user(request)
        elif action == 'update':
            return self.update_user(request)
        elif action == 'delete':
            return self.delete_user(request)
        else:
            return self.update_user_status(request)
    
    def create_user(self, request):
        """Create new user"""
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            role = request.data.get('role', 'student')
            
            if not all([username, email, password]):
                return Response(
                    {'error': 'Username, email, and password are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Username already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='user_management',
                action_description=f'Created user {user.username}',
                target_model='User',
                target_id=user.id,
                action_data={'action': 'create', 'username': username, 'email': email, 'role': role},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'User {username} created successfully'})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create user: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update_user(self, request):
        """Update user information"""
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Update fields
            if 'username' in request.data:
                new_username = request.data['username']
                if User.objects.filter(username=new_username).exclude(id=user_id).exists():
                    return Response(
                        {'error': 'Username already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.username = new_username
            
            if 'email' in request.data:
                new_email = request.data['email']
                if User.objects.filter(email=new_email).exclude(id=user_id).exists():
                    return Response(
                        {'error': 'Email already exists'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.email = new_email
            
            if 'role' in request.data:
                user.role = request.data['role']
            
            if 'is_staff' in request.data:
                user.is_staff = request.data['is_staff']
            
            user.save()
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='user_management',
                action_description=f'Updated user {user.username}',
                target_model='User',
                target_id=user.id,
                action_data={'action': 'update', 'updated_fields': list(request.data.keys())},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'User {user.username} updated successfully'})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to update user: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete_user(self, request):
        """Delete user"""
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Prevent deleting self
            if user.id == request.user.id:
                return Response(
                    {'error': 'Cannot delete your own account'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            username = user.username
            user.delete()
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='user_management',
                action_description=f'Deleted user {username}',
                target_model='User',
                target_id=user_id,
                action_data={'action': 'delete', 'username': username},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'User {username} deleted successfully'})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to delete user: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update_user_status(self, request):
        """Update user status (activate/deactivate/make_staff)"""
        user_id = request.data.get('user_id')
        action = request.data.get('action')  # 'activate', 'deactivate', 'make_staff', 'remove_staff'
        
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

class MentorApplicationsView(generics.GenericAPIView):
    """Mentor applications management"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get mentor applications list"""
        from mentors.models import MentorApplication
        
        applications = MentorApplication.objects.select_related('user').values(
            'id', 'user__id', 'user__username', 'user__email', 'user__first_name', 'user__last_name',
            'status', 'motivation', 'relevant_experience', 'preferred_payment_method',
            'created_at', 'reviewed_at', 'reviewed_by__username'
        )
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter and status_filter != 'all':
            applications = applications.filter(status=status_filter)
        
        # Apply search
        search_term = request.query_params.get('search')
        if search_term:
            applications = applications.filter(
                Q(user__username__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term)
            )
        
        serializer = MentorApplicationsSerializer(applications, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Handle mentor application actions"""
        action = request.data.get('action')
        
        if action == 'approve':
            return self.approve_application(request)
        elif action == 'reject':
            return self.reject_application(request)
        else:
            return Response(
                {'error': 'Invalid action'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def approve_application(self, request):
        """Approve mentor application"""
        try:
            application_id = request.data.get('application_id')
            from mentors.models import MentorApplication
            
            application = MentorApplication.objects.get(id=application_id)
            
            if application.status != 'pending':
                return Response(
                    {'error': 'Application is not pending'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Approve the application
            application.approve(request.user)
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='mentor_management',
                action_description=f'Approved mentor application for {application.user.username}',
                target_model='MentorApplication',
                target_id=application.id,
                action_data={'action': 'approve', 'user_id': application.user.id},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'Mentor application approved successfully'})
            
        except MentorApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to approve application: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def reject_application(self, request):
        """Reject mentor application"""
        try:
            application_id = request.data.get('application_id')
            rejection_reason = request.data.get('rejection_reason', '')
            
            from mentors.models import MentorApplication
            
            application = MentorApplication.objects.get(id=application_id)
            
            if application.status != 'pending':
                return Response(
                    {'error': 'Application is not pending'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reject the application
            application.reject(request.user, rejection_reason)
            
            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='mentor_management',
                action_description=f'Rejected mentor application for {application.user.username}',
                target_model='MentorApplication',
                target_id=application.id,
                action_data={'action': 'reject', 'user_id': application.user.id, 'reason': rejection_reason},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'message': f'Mentor application rejected successfully'})
            
        except MentorApplication.DoesNotExist:
            return Response(
                {'error': 'Application not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to reject application: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
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
            'external_services': [
                {
                    'name': 'email_service',
                    'status': 'healthy',
                    'response_time': 150,
                    'last_check': timezone.now().isoformat()
                },
                {
                    'name': 'payment_service',
                    'status': 'healthy',
                    'response_time': 200,
                    'last_check': timezone.now().isoformat()
                },
                {
                    'name': 'ai_service',
                    'status': 'healthy',
                    'response_time': 300,
                    'last_check': timezone.now().isoformat()
                }
            ],
            'system_metrics': {
                'cpu_usage': 23.1,
                'memory_usage': 67.8,
                'disk_usage': 45.2,
                'active_connections': 15
            },
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(data)
