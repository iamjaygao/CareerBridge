from django.contrib import admin
from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, NotificationBatch
)
from django.utils import timezone

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'is_sent', 'priority', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_sent', 'priority', 'created_at']
    search_fields = ['user__username', 'user__email', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'read_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'title', 'message', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'sent_at', 'read_at')
        }),
        ('Related Objects', {
            'fields': ('related_appointment', 'related_resume', 'related_mentor'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_sent', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as sent.')
    mark_as_sent.short_description = "Mark selected notifications as sent"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'notification_type', 'is_active', 'created_at']
    list_filter = ['template_type', 'notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'title_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'notification_type', 'is_active')
        }),
        ('Template Content', {
            'fields': ('subject', 'title_template', 'message_template')
        }),
        ('Template Variables', {
            'fields': ('variables',),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'sms_notifications', 'push_notifications', 'in_app_notifications']
    list_filter = ['email_notifications', 'sms_notifications', 'push_notifications', 'in_app_notifications']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Email Notifications', {
            'fields': (
                'email_notifications', 'email_appointment_reminders', 'email_mentor_responses',
                'email_payment_notifications', 'email_system_announcements'
            )
        }),
        ('SMS Notifications', {
            'fields': (
                'sms_notifications', 'sms_appointment_reminders', 'sms_urgent_notifications'
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_notifications', 'push_appointment_reminders', 'push_mentor_responses',
                'push_job_matches'
            )
        }),
        ('In-App Notifications', {
            'fields': ('in_app_notifications',)
        }),
        ('Time Settings', {
            'fields': ('reminder_advance_hours', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'delivery_method', 'delivery_status', 'recipient', 'retry_count', 'created_at']
    list_filter = ['delivery_method', 'delivery_status', 'retry_count', 'created_at']
    search_fields = ['notification__title', 'recipient', 'subject']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification', 'delivery_method', 'delivery_status', 'recipient')
        }),
        ('Delivery Content', {
            'fields': ('subject', 'content'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('created_at', 'sent_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_sent', 'mark_as_delivered', 'mark_as_failed']
    
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(delivery_status='sent', sent_at=timezone.now())
        self.message_user(request, f'{updated} logs marked as sent.')
    mark_as_sent.short_description = "Mark selected logs as sent"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(delivery_status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} logs marked as delivered.')
    mark_as_delivered.short_description = "Mark selected logs as delivered"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(delivery_status='failed')
        self.message_user(request, f'{updated} logs marked as failed.')
    mark_as_failed.short_description = "Mark selected logs as failed"

@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'status', 'total_count', 'sent_count', 'failed_count', 'progress_percentage', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['name']
    readonly_fields = ['total_count', 'sent_count', 'failed_count', 'progress_percentage', 'created_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'template', 'status')
        }),
        ('Target Users', {
            'fields': ('target_users', 'target_criteria'),
            'classes': ('collapse',)
        }),
        ('Progress Statistics', {
            'fields': ('total_count', 'sent_count', 'failed_count', 'progress_percentage')
        }),
        ('Time Information', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing', started_at=timezone.now())
        self.message_user(request, f'{updated} batches marked as processing.')
    mark_as_processing.short_description = "Mark selected batches as processing"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} batches marked as completed.')
    mark_as_completed.short_description = "Mark selected batches as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed', completed_at=timezone.now())
        self.message_user(request, f'{updated} batches marked as failed.')
    mark_as_failed.short_description = "Mark selected batches as failed"
