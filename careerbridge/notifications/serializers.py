from rest_framework import serializers
from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, NotificationBatch
)

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    target_role_display = serializers.CharField(source='get_target_role_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display', 'title', 'message',
            'is_read', 'is_sent', 'priority', 'priority_display', 'target_role', 'target_role_display',
            'related_appointment', 'related_resume', 'related_mentor', 'sent_at', 'read_at', 'created_at', 'payload'
        ]
        read_only_fields = [
            'id', 'user', 'target_role', 'notification_type', 'title', 'message', 'priority',
            'related_appointment', 'related_resume', 'related_mentor', 'sent_at',
            'read_at', 'created_at'
        ]

class NotificationListSerializer(serializers.ModelSerializer):
    """Notification list serializer (simplified version)"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    target_role_display = serializers.CharField(source='get_target_role_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display', 'title', 'message',
            'is_read', 'priority', 'priority_display', 'target_role', 'target_role_display',
            'created_at', 'payload'
        ]
        read_only_fields = fields

class NotificationMarkReadSerializer(serializers.Serializer):
    """Mark notifications as read"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of notification IDs to mark as read"
    )
    
    def validate_notification_ids(self, value):
        """Validate notification ID list"""
        from django.db.models import Q
        user = self.context['request'].user
        user_role = getattr(user, 'role', None)
        valid_ids = Notification.objects.filter(
            Q(user=user) | Q(target_role=user_role),
            id__in=value
        ).values_list('id', flat=True)
        
        if len(valid_ids) != len(value):
            raise serializers.ValidationError("Some notification IDs are invalid")
        
        return value

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Notification preference serializer"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications', 'email_appointment_reminders', 'email_mentor_responses',
            'email_payment_notifications', 'email_system_announcements',
            'sms_notifications', 'sms_appointment_reminders', 'sms_urgent_notifications',
            'push_notifications', 'push_appointment_reminders', 'push_mentor_responses',
            'push_job_matches', 'in_app_notifications', 'reminder_advance_hours',
            'quiet_hours_start', 'quiet_hours_end'
        ]
    
    def validate_reminder_advance_hours(self, value):
        """Validate reminder advance hours"""
        if value < 1 or value > 168:  # 1 hour to 1 week
            raise serializers.ValidationError("Reminder advance hours must be between 1 and 168")
        return value

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Notification template serializer"""
    
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display', 'notification_type',
            'notification_type_display', 'subject', 'title_template', 'message_template',
            'variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class NotificationLogSerializer(serializers.ModelSerializer):
    """Notification log serializer"""
    
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    delivery_status_display = serializers.CharField(source='get_delivery_status_display', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'delivery_method', 'delivery_method_display',
            'delivery_status', 'delivery_status_display', 'recipient', 'subject',
            'content', 'error_message', 'retry_count', 'created_at', 'sent_at', 'delivered_at'
        ]
        read_only_fields = fields

class NotificationBatchSerializer(serializers.ModelSerializer):
    """Batch notification task serializer"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display', 'template',
            'target_users', 'target_criteria', 'status', 'status_display', 'total_count',
            'sent_count', 'failed_count', 'progress_percentage', 'created_at', 'started_at',
            'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'total_count', 'sent_count', 'failed_count', 'progress_percentage',
            'created_at', 'started_at', 'completed_at'
        ]

class NotificationStatsSerializer(serializers.Serializer):
    """Notification statistics serializer"""
    
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()
    recent_notifications = NotificationListSerializer(many=True)

class NotificationCreateSerializer(serializers.ModelSerializer):
    """Create notification serializer"""
    
    class Meta:
        model = Notification
        fields = [
            'user', 'target_role', 'notification_type', 'title', 'message', 'priority',
            'related_appointment', 'related_resume', 'related_mentor'
        ]
    
    def validate(self, data):
        """Validate that either user or target_role is set"""
        if not data.get('user') and not data.get('target_role'):
            raise serializers.ValidationError("Either 'user' or 'target_role' must be set")
        return data
    
    def validate_user(self, value):
        """Validate user"""
        request = self.context.get('request')
        if request and not request.user.is_staff:
            # Non-admin users can only create notifications for themselves
            if value != request.user:
                raise serializers.ValidationError("You can only create notifications for yourself")
        return value

class NotificationFilterSerializer(serializers.Serializer):
    """Notification filter serializer"""
    
    notification_type = serializers.ChoiceField(
        choices=Notification.NOTIFICATION_TYPE_CHOICES,
        required=False
    )
    is_read = serializers.BooleanField(required=False)
    priority = serializers.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, required=False)
