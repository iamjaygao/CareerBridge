from rest_framework import serializers
from .models import (
    SystemStats, AdminAction, SystemConfig, DataExport, ContentModeration, SystemSettings
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
    """Dashboard statistics serializer - aggregated metrics only, no user data"""
    
    # ==================== PLATFORM OVERVIEW ====================
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_mentors = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    total_staff = serializers.IntegerField()
    
    # ==================== MONTHLY METRICS WITH MoM/YoY ====================
    new_users_this_month = serializers.IntegerField()
    user_mom = serializers.FloatField(allow_null=True)
    user_yoy = serializers.FloatField(allow_null=True)
    
    new_students_this_month = serializers.IntegerField()
    student_mom = serializers.FloatField(allow_null=True)
    student_yoy = serializers.FloatField(allow_null=True)
    
    new_mentors_this_month = serializers.IntegerField()
    mentor_mom = serializers.FloatField(allow_null=True)
    mentor_yoy = serializers.FloatField(allow_null=True)
    
    new_staff_this_month = serializers.IntegerField()
    staff_mom = serializers.FloatField(allow_null=True)
    staff_yoy = serializers.FloatField(allow_null=True)
    
    # ==================== APPOINTMENT METRICS ====================
    appointments_this_month = serializers.IntegerField()
    appointments_last_month_same_period = serializers.IntegerField()
    appointment_mom = serializers.FloatField(allow_null=True)
    appointment_yoy = serializers.FloatField(allow_null=True)
    cancellation_rate = serializers.FloatField()
    
    # ==================== RESUME METRICS ====================
    resumes_uploaded_this_month = serializers.IntegerField()
    resume_mom = serializers.FloatField(allow_null=True)
    resume_yoy = serializers.FloatField(allow_null=True)
    
    # ==================== TREND DATASETS (7-DAY) ====================
    users_7_day = serializers.ListField()
    mentors_7_day = serializers.ListField()
    appointments_7_day = serializers.ListField()
    resumes_7_day = serializers.ListField()
    
    # ==================== OPERATIONAL METRICS ====================
    active_mentors = serializers.IntegerField()
    pending_mentor_approvals = serializers.IntegerField()
    pending_resume_reviews = serializers.IntegerField()
    active_admins_today = serializers.IntegerField()
    active_staff_today = serializers.IntegerField()
    
    # ==================== LEGACY FIELDS (for backward compatibility) ====================
    students = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    pending_applications = serializers.IntegerField()
    appointments = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    completed_today = serializers.IntegerField()
    assessments = serializers.IntegerField()
    job_listings = serializers.IntegerField()
    
    # System health and performance
    system_health = serializers.CharField()
    avg_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime_percentage = serializers.FloatField()
    
    # Financial statistics
    revenue_today = serializers.FloatField()
    total_revenue = serializers.FloatField()
    mentor_earnings = serializers.FloatField()
    platform_earnings = serializers.FloatField()
    pending_payouts = serializers.FloatField()
    revenue_trend = serializers.ListField()

class UserManagementSerializer(serializers.Serializer):
    """User management serializer"""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    role = serializers.CharField()
    date_joined = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True, required=False)
    total_appointments = serializers.IntegerField()
    total_resumes = serializers.IntegerField()

class MentorApplicationsSerializer(serializers.Serializer):
    """Mentor applications serializer"""
    
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = serializers.CharField()
    motivation = serializers.CharField()
    relevant_experience = serializers.CharField()
    preferred_payment_method = serializers.CharField()
    created_at = serializers.DateTimeField()
    reviewed_at = serializers.DateTimeField(allow_null=True)
    reviewed_by = serializers.CharField(allow_null=True)

class MentorManagementSerializer(serializers.Serializer):
    """Mentor management serializer"""
    
    mentor_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    status = serializers.CharField()
    is_approved = serializers.BooleanField()
    is_verified = serializers.BooleanField()
    verification_badge = serializers.CharField(required=False, allow_blank=True)
    specializations = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    years_of_experience = serializers.IntegerField(required=False)
    total_sessions = serializers.IntegerField()
    average_rating = serializers.FloatField()
    hourly_rate = serializers.FloatField(required=False, allow_null=True)
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


class SystemSettingsSerializer(serializers.ModelSerializer):
    """System settings serializer with API key masking"""
    
    # Masked API keys (read-only)
    openai_api_key_masked = serializers.SerializerMethodField()
    stripe_secret_key_masked = serializers.SerializerMethodField()
    email_api_key_masked = serializers.SerializerMethodField()
    google_oauth_key_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSettings
        fields = [
            # Platform Settings
            'platform_name', 'company_name', 'support_email', 'support_phone',
            'office_address', 'website_url',
            # Contact Settings
            'contact_title', 'contact_description',
            # Announcement Settings
            'announcement_enabled', 'announcement_text', 'announcement_type',
            # Appearance Settings
            'primary_color', 'accent_color', 'logo_url', 'favicon_url', 'theme',
            # Contact & Social Links
            'linkedin_url', 'twitter_url', 'instagram_url', 'youtube_url', 'facebook_url',
            # API Keys (masked)
            'openai_api_key', 'stripe_secret_key', 'email_api_key', 'google_oauth_key',
            'openai_api_key_masked', 'stripe_secret_key_masked', 
            'email_api_key_masked', 'google_oauth_key_masked',
            # Email Configuration
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_from_name', 'template_footer_text',
            # Timestamps
            'created_at', 'updated_at', 'updated_by',
        ]
        read_only_fields = ['created_at', 'updated_at', 'updated_by']
    
    def get_openai_api_key_masked(self, obj):
        """Return masked OpenAI API key"""
        if obj.openai_api_key:
            return self._mask_key(obj.openai_api_key)
        return None
    
    def get_stripe_secret_key_masked(self, obj):
        """Return masked Stripe secret key"""
        if obj.stripe_secret_key:
            return self._mask_key(obj.stripe_secret_key)
        return None
    
    def get_email_api_key_masked(self, obj):
        """Return masked email API key"""
        if obj.email_api_key:
            return self._mask_key(obj.email_api_key)
        return None
    
    def get_google_oauth_key_masked(self, obj):
        """Return masked Google OAuth key"""
        if obj.google_oauth_key:
            return self._mask_key(obj.google_oauth_key)
        return None
    
    def _mask_key(self, key_value):
        """Mask API key (show first 4 and last 4 characters)"""
        if not key_value or len(key_value) < 8:
            return '****'
        return f"{key_value[:4]}****{key_value[-4:]}"
    
    def to_representation(self, instance):
        """Override to always return masked keys in GET requests"""
        data = super().to_representation(instance)
        # Replace actual keys with masked versions in response
        if instance.openai_api_key:
            data['openai_api_key'] = self._mask_key(instance.openai_api_key)
        if instance.stripe_secret_key:
            data['stripe_secret_key'] = self._mask_key(instance.stripe_secret_key)
        if instance.email_api_key:
            data['email_api_key'] = self._mask_key(instance.email_api_key)
        if instance.google_oauth_key:
            data['google_oauth_key'] = self._mask_key(instance.google_oauth_key)
        return data 