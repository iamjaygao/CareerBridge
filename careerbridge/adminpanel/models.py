from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

class SystemStats(models.Model):
    """System statistics information"""
    
    # User statistics
    total_users = models.PositiveIntegerField(default=0, help_text="Total number of users")
    active_users_today = models.PositiveIntegerField(default=0, help_text="Active users today")
    active_users_week = models.PositiveIntegerField(default=0, help_text="Active users this week")
    active_users_month = models.PositiveIntegerField(default=0, help_text="Active users this month")
    new_users_today = models.PositiveIntegerField(default=0, help_text="New users today")
    new_users_week = models.PositiveIntegerField(default=0, help_text="New users this week")
    new_users_month = models.PositiveIntegerField(default=0, help_text="New users this month")
    
    # Mentor statistics
    total_mentors = models.PositiveIntegerField(default=0, help_text="Total number of mentors")
    active_mentors = models.PositiveIntegerField(default=0, help_text="Active mentors")
    pending_mentor_applications = models.PositiveIntegerField(default=0, help_text="Pending mentor applications")
    
    # Appointment statistics
    total_appointments = models.PositiveIntegerField(default=0, help_text="Total number of appointments")
    appointments_today = models.PositiveIntegerField(default=0, help_text="Appointments today")
    appointments_week = models.PositiveIntegerField(default=0, help_text="Appointments this week")
    appointments_month = models.PositiveIntegerField(default=0, help_text="Appointments this month")
    completed_appointments = models.PositiveIntegerField(default=0, help_text="Completed appointments")
    cancelled_appointments = models.PositiveIntegerField(default=0, help_text="Cancelled appointments")
    
    # Resume statistics
    total_resumes = models.PositiveIntegerField(default=0, help_text="Total number of resumes")
    resumes_analyzed_today = models.PositiveIntegerField(default=0, help_text="Resumes analyzed today")
    resumes_analyzed_week = models.PositiveIntegerField(default=0, help_text="Resumes analyzed this week")
    resumes_analyzed_month = models.PositiveIntegerField(default=0, help_text="Resumes analyzed this month")
    
    # Revenue statistics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total revenue")
    revenue_today = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Revenue today")
    revenue_week = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Revenue this week")
    revenue_month = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Revenue this month")
    
    # System performance
    avg_response_time = models.FloatField(default=0, help_text="Average response time (ms)")
    error_rate = models.FloatField(default=0, help_text="Error rate (%)")
    uptime_percentage = models.FloatField(default=100, help_text="System availability (%)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Stats"
        verbose_name_plural = "System Stats"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"System Stats - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class AdminAction(models.Model):
    """Admin action log"""
    
    ACTION_TYPE_CHOICES = (
        ('user_management', 'User management'),
        ('mentor_management', 'Mentor management'),
        ('appointment_management', 'Appointment management'),
        ('resume_management', 'Resume management'),
        ('system_config', 'System configuration'),
        ('data_export', 'Data export'),
        ('notification_send', 'Send notification'),
        ('payment_management', 'Payment management'),
        ('content_moderation', 'Content moderation'),
        ('security_audit', 'Security audit'),
    )
    
    # Basic information
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    action_description = models.TextField(help_text="Action description")
    
    # Action details
    target_model = models.CharField(max_length=100, blank=True, help_text="Target model")
    target_id = models.IntegerField(null=True, blank=True, help_text="Target object ID")
    action_data = models.JSONField(default=dict, help_text="Action data")
    
    # IP and user agent
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address")
    user_agent = models.TextField(blank=True, help_text="User agent")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_type_display()} - {self.created_at}"

class SystemConfig(models.Model):
    """System configuration"""
    
    CONFIG_TYPE_CHOICES = (
        ('general', 'General configuration'),
        ('email', 'Email configuration'),
        ('payment', 'Payment configuration'),
        ('notification', 'Notification configuration'),
        ('security', 'Security configuration'),
        ('feature_flags', 'Feature flags'),
    )
    
    # Basic information
    key = models.CharField(max_length=100, unique=True, help_text="Configuration key")
    value = models.TextField(help_text="Configuration value")
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES, default='general')
    description = models.TextField(blank=True, help_text="Configuration description")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Is active")
    is_sensitive = models.BooleanField(default=False, help_text="Is sensitive information")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='config_updates'
    )
    
    class Meta:
        ordering = ['config_type', 'key']
        indexes = [
            models.Index(fields=['config_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.get_config_type_display()})"

class DataExport(models.Model):
    """Data export task"""
    
    EXPORT_TYPE_CHOICES = (
        ('users', 'User data'),
        ('mentors', 'Mentor data'),
        ('appointments', 'Appointment data'),
        ('resumes', 'Resume data'),
        ('notifications', 'Notification data'),
        ('payments', 'Payment data'),
        ('system_logs', 'System logs'),
    )
    
    FORMAT_CHOICES = (
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    # Basic information
    name = models.CharField(max_length=200, help_text="Export task name")
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='csv')
    
    # Filter conditions
    date_from = models.DateField(null=True, blank=True, help_text="Start date")
    date_to = models.DateField(null=True, blank=True, help_text="End date")
    filters = models.JSONField(default=dict, help_text="Filter conditions")
    
    # Status and result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True, help_text="File path")
    file_size = models.PositiveIntegerField(default=0, help_text="File size (bytes)")
    record_count = models.PositiveIntegerField(default=0, help_text="Record count")
    
    # Error information
    error_message = models.TextField(blank=True, help_text="Error message")
    
    # User information
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_exports')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_count == 0:
            return 0
        return (self.sent_count + self.failed_count) / self.total_count * 100

class ContentModeration(models.Model):
    """Content moderation"""
    
    CONTENT_TYPE_CHOICES = (
        ('mentor_profile', 'Mentor profile'),
        ('user_review', 'User review'),
        ('appointment_notes', 'Appointment notes'),
        ('resume_content', 'Resume content'),
        ('system_announcement', 'System announcement'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    )
    
    # Basic information
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.IntegerField(help_text="Content ID")
    content_preview = models.TextField(help_text="Content preview")
    
    # Moderation information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    flagged_reason = models.TextField(blank=True, help_text="Flagged reason")
    moderation_notes = models.TextField(blank=True, help_text="Moderation notes")
    
    # Reviewer
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='content_moderations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()} - {self.content_id} - {self.get_status_display()}"
