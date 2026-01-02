from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Notification(models.Model):
    """User notification model"""
    
    NOTIFICATION_TYPE_CHOICES = (
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmed', 'Appointment Confirmed'),
        ('appointment_rejected', 'Appointment Rejected'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('appointment_expired', 'Appointment Expired'),
        ('appointment_rescheduled', 'Appointment Rescheduled'),
        ('mentor_response', 'Mentor Response'),
        ('feedback_submitted', 'Feedback Submitted'),
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('system_announcement', 'System Announcement'),
        ('mentor_application_submitted', 'Mentor Application Submitted'),
        ('mentor_application_approved', 'Mentor Application Approved'),
        ('mentor_application_rejected', 'Mentor Application Rejected'),
        ('resume_uploaded', 'Resume Uploaded'),
        ('support_ticket_created', 'Support Ticket Created'),
        ('staff_appointment_cancelled', 'Staff Appointment Cancelled'),
        ('staff_payment_failed', 'Staff Payment Failed'),
        ('staff_user_feedback_submitted', 'Staff User Feedback Submitted'),
        ('staff_user_reported', 'Staff User Reported'),
        ('staff_chat_no_response', 'Staff Chat No Response'),
        ('staff_appointment_upcoming', 'Staff Appointment Upcoming'),
        ('staff_mentor_no_confirm', 'Staff Mentor No Confirm'),
        ('staff_mentor_no_feedback', 'Staff Mentor No Feedback'),
        ('staff_repeat_failure', 'Staff Repeat Failure'),
        ('admin_mentor_profile_updated', 'Admin Mentor Profile Updated'),
        ('admin_risk_alert', 'Admin Risk Alert'),
        ('admin_slot_conflict', 'Admin Slot Conflict'),
        ('admin_refund_alert', 'Admin Refund Alert'),
        ('admin_mentor_low_rating', 'Admin Mentor Low Rating'),
        ('admin_metric_anomaly', 'Admin Metric Anomaly'),
        ('admin_payment_success_drop', 'Admin Payment Success Drop'),
        ('superadmin_system_alert', 'Superadmin System Alert'),
        ('superadmin_security_alert', 'Superadmin Security Alert'),
        ('superadmin_rule_change', 'Superadmin Rule Change'),
        ('resume_analysis_complete', 'Resume Analysis Complete'),
        ('job_match_found', 'Job Match Found'),
        ('referral_reward', 'Referral Reward'),
        ('subscription_expiry', 'Subscription Expiry'),
        ('welcome', 'Welcome Message'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('urgent', 'Urgent'),
    )
    
    TARGET_ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
    )
    
    # Target information - either specific user OR role-based
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Specific user target (if null, targets all users with target_role)"
    )
    target_role = models.CharField(
        max_length=20,
        choices=TARGET_ROLE_CHOICES,
        null=True,
        blank=True,
        help_text="Role-based target (if user is null, all users with this role see it)"
    )
    
    # Basic information
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification content")
    
    # Status and priority
    is_read = models.BooleanField(default=False, help_text="Whether read")
    is_sent = models.BooleanField(default=False, help_text="Whether sent")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Related objects
    related_appointment = models.ForeignKey('decision_slots.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    related_resume = models.ForeignKey('ats_signals.Resume', on_delete=models.SET_NULL, null=True, blank=True)
    related_mentor = models.ForeignKey('human_loop.MentorProfile', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Delivery information
    sent_at = models.DateTimeField(null=True, blank=True, help_text="Sent time")
    read_at = models.DateTimeField(null=True, blank=True, help_text="Read time")
    
    # Action payload for deep-linking
    payload = models.JSONField(default=dict, blank=True, help_text="Action payload for navigation")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['target_role', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        target = self.user.username if self.user else f"Role: {self.target_role}"
        return f"{target} - {self.title}"
    
    def clean(self):
        """Validate that either user or target_role is set"""
        from django.core.exceptions import ValidationError
        if not self.user and not self.target_role:
            raise ValidationError("Either 'user' or 'target_role' must be set")
    
    def mark_as_read(self):
        """Mark as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self):
        """Mark as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save()

class NotificationTemplate(models.Model):
    """Notification template"""
    
    TEMPLATE_TYPE_CHOICES = (
        ('email', 'Email Template'),
        ('sms', 'SMS Template'),
        ('push', 'Push Template'),
        ('in_app', 'In-App Template'),
    )
    
    name = models.CharField(max_length=100, help_text="Template name")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    notification_type = models.CharField(max_length=50, choices=Notification.NOTIFICATION_TYPE_CHOICES)
    
    # Template content
    subject = models.CharField(max_length=200, blank=True, help_text="Email subject")
    title_template = models.CharField(max_length=200, help_text="Title template")
    message_template = models.TextField(help_text="Message template")
    
    # Template variables description
    variables = models.JSONField(default=dict, help_text="Template variables description")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether enabled")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['template_type', 'notification_type']
        ordering = ['template_type', 'notification_type']
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"

class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notification settings
    email_notifications = models.BooleanField(default=True, help_text="Enable email notifications")
    email_appointment_reminders = models.BooleanField(default=True, help_text="Appointment reminder emails")
    email_mentor_responses = models.BooleanField(default=True, help_text="Mentor response emails")
    email_payment_notifications = models.BooleanField(default=True, help_text="Payment notification emails")
    email_system_announcements = models.BooleanField(default=True, help_text="System announcement emails")
    
    # SMS notification settings
    sms_notifications = models.BooleanField(default=False, help_text="Enable SMS notifications")
    sms_appointment_reminders = models.BooleanField(default=False, help_text="Appointment reminder SMS")
    sms_urgent_notifications = models.BooleanField(default=True, help_text="Urgent notification SMS")
    
    # Push notification settings
    push_notifications = models.BooleanField(default=True, help_text="Enable push notifications")
    push_appointment_reminders = models.BooleanField(default=True, help_text="Appointment reminder push")
    push_mentor_responses = models.BooleanField(default=True, help_text="Mentor response push")
    push_job_matches = models.BooleanField(default=True, help_text="Job match push")
    
    # In-app notification settings
    in_app_notifications = models.BooleanField(default=True, help_text="Enable in-app notifications")
    
    # Time settings
    reminder_advance_hours = models.PositiveIntegerField(default=24, help_text="Appointment reminder advance hours")
    quiet_hours_start = models.TimeField(default='22:00', help_text="Quiet hours start time")
    quiet_hours_end = models.TimeField(default='08:00', help_text="Quiet hours end time")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"{self.user.username} - Notification Preferences"
    
    def is_quiet_hours(self):
        """Check if currently in quiet hours"""
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Cross midnight
            return now >= start or now <= end

class NotificationLog(models.Model):
    """Notification delivery log"""
    
    DELIVERY_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    delivery_method = models.CharField(max_length=20, choices=NotificationTemplate.TEMPLATE_TYPE_CHOICES)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    
    # Delivery details
    recipient = models.CharField(max_length=255, help_text="Recipient")
    subject = models.CharField(max_length=200, blank=True, help_text="Subject")
    content = models.TextField(help_text="Delivery content")
    
    # Error information
    error_message = models.TextField(blank=True, help_text="Error message")
    retry_count = models.PositiveIntegerField(default=0, help_text="Retry count")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delivery_method', 'delivery_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} - {self.delivery_method} - {self.delivery_status}"
    
    def mark_as_sent(self):
        """Mark as sent"""
        self.delivery_status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        """Mark as delivered"""
        self.delivery_status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message=""):
        """Mark as failed"""
        self.delivery_status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()

class NotificationBatch(models.Model):
    """Batch notification task"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    name = models.CharField(max_length=100, help_text="Batch task name")
    notification_type = models.CharField(max_length=50, choices=Notification.NOTIFICATION_TYPE_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Target users
    target_users = models.JSONField(default=list, help_text="Target user ID list")
    target_criteria = models.JSONField(default=dict, help_text="Target user filter criteria")
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_count = models.PositiveIntegerField(default=0, help_text="Total count")
    sent_count = models.PositiveIntegerField(default=0, help_text="Sent count")
    failed_count = models.PositiveIntegerField(default=0, help_text="Failed count")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_count == 0:
            return 0
        return (self.sent_count + self.failed_count) / self.total_count * 100
