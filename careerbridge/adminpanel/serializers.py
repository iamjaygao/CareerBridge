from rest_framework import serializers
from .models import (
    SystemStats, AdminAction, SystemConfig, DataExport, ContentModeration
)
from django.utils import timezone

class SystemStatsSerializer(serializers.ModelSerializer):
    """System statistics serializer"""
    
    class Meta:
        model = SystemStats
        fields = [
            'id', 'total_users', 'active_users_today', 'active_users_week', 'active_users_month',
            'new_users_today', 'new_users_week', 'new_users_month', 'total_mentors', 'active_mentors',
            'pending_mentor_applications', 'total_appointments', 'appointments_today',
            'appointments_week', 'appointments_month', 'completed_appointments', 'cancelled_appointments',
            'total_resumes', 'resumes_analyzed_today', 'resumes_analyzed_week', 'resumes_analyzed_month',
            'total_revenue', 'revenue_today', 'revenue_week', 'revenue_month', 'avg_response_time',
            'error_rate', 'uptime_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class AdminActionSerializer(serializers.ModelSerializer):
    """Admin action log serializer"""
    
    admin_user = serializers.StringRelatedField()
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = AdminAction
        fields = [
            'id', 'admin_user', 'action_type', 'action_type_display', 'action_description',
            'target_model', 'target_id', 'action_data', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = fields

class SystemConfigSerializer(serializers.ModelSerializer):
    """System configuration serializer"""
    
    config_type_display = serializers.CharField(source='get_config_type_display', read_only=True)
    updated_by = serializers.StringRelatedField()
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'config_type', 'config_type_display', 'description',
            'is_active', 'is_sensitive', 'created_at', 'updated_at', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def validate_key(self, value):
        """Validate the uniqueness of the configuration key"""
        if SystemConfig.objects.filter(key=value).exists():
            raise serializers.ValidationError("Configuration key already exists")
        return value

class SystemConfigUpdateSerializer(serializers.ModelSerializer):
    """System configuration update serializer"""
    
    class Meta:
        model = SystemConfig
        fields = ['value', 'description', 'is_active']
    
    def update(self, instance, validated_data):
        """Update configuration and record updater"""
        instance.updated_by = self.context['request'].user
        return super().update(instance, validated_data)

class DataExportSerializer(serializers.ModelSerializer):
    """Data export serializer"""
    
    export_type_display = serializers.CharField(source='get_export_type_display', read_only=True)
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requested_by = serializers.StringRelatedField()
    
    class Meta:
        model = DataExport
        fields = [
            'id', 'name', 'export_type', 'export_type_display', 'format', 'format_display',
            'date_from', 'date_to', 'filters', 'status', 'status_display', 'file_path',
            'file_size', 'record_count', 'error_message', 'requested_by', 'created_at',
            'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'file_size', 'record_count', 'error_message',
            'requested_by', 'created_at', 'started_at', 'completed_at'
        ]

class DataExportCreateSerializer(serializers.ModelSerializer):
    """Data export creation serializer"""
    
    class Meta:
        model = DataExport
        fields = [
            'name', 'export_type', 'format', 'date_from', 'date_to', 'filters'
        ]
    
    def validate(self, data):
        """Validate export parameters"""
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError("Start date must be before end date")
        return data
    
    def create(self, validated_data):
        """Create export task"""
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)

class ContentModerationSerializer(serializers.ModelSerializer):
    """Content moderation serializer"""
    
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by = serializers.StringRelatedField()
    
    class Meta:
        model = ContentModeration
        fields = [
            'id', 'content_type', 'content_type_display', 'content_id', 'content_preview',
            'status', 'status_display', 'flagged_reason', 'moderation_notes', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'content_type', 'content_id', 'content_preview', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]

class ContentModerationUpdateSerializer(serializers.ModelSerializer):
    """Content moderation update serializer"""
    
    class Meta:
        model = ContentModeration
        fields = ['status', 'flagged_reason', 'moderation_notes']
    
    def update(self, instance, validated_data):
        """Update moderation status and record reviewer"""
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        return super().update(instance, validated_data)

class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    # User statistics
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    # Mentor statistics
    total_mentors = serializers.IntegerField()
    active_mentors = serializers.IntegerField()
    pending_applications = serializers.IntegerField()
    # Appointment statistics
    total_appointments = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    completed_today = serializers.IntegerField()
    # Revenue statistics
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    # System performance
    avg_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime_percentage = serializers.FloatField()

class UserManagementSerializer(serializers.Serializer):
    """User management serializer"""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    date_joined = serializers.DateTimeField()
    last_login = serializers.DateTimeField()
    total_appointments = serializers.IntegerField()
    total_resumes = serializers.IntegerField()

class MentorManagementSerializer(serializers.Serializer):
    """Mentor management serializer"""
    
    mentor_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    status = serializers.CharField()
    is_approved = serializers.BooleanField()
    total_sessions = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)

class AppointmentManagementSerializer(serializers.Serializer):
    """Appointment management serializer"""
    
    appointment_id = serializers.IntegerField()
    user_username = serializers.CharField()
    mentor_name = serializers.CharField()
    title = serializers.CharField()
    status = serializers.CharField()
    scheduled_start = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    is_paid = serializers.BooleanField()

class SystemHealthSerializer(serializers.Serializer):
    """System health status serializer"""
    
    database_status = serializers.CharField()
    cache_status = serializers.CharField()
    external_services_status = serializers.DictField()
    disk_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    active_connections = serializers.IntegerField()
    error_count_last_hour = serializers.IntegerField() 