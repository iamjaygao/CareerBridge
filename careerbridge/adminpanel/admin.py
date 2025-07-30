from django.contrib import admin
from .models import (
    SystemStats, AdminAction, SystemConfig, DataExport, ContentModeration
)

@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'total_users', 'total_mentors', 'total_appointments',
        'total_revenue', 'avg_response_time', 'error_rate', 'uptime_percentage'
    ]
    list_filter = ['created_at']
    readonly_fields = [
        'total_users', 'active_users_today', 'active_users_week', 'active_users_month',
        'new_users_today', 'new_users_week', 'new_users_month', 'total_mentors',
        'active_mentors', 'pending_mentor_applications', 'total_appointments',
        'appointments_today', 'appointments_week', 'appointments_month',
        'completed_appointments', 'cancelled_appointments', 'total_resumes',
        'resumes_analyzed_today', 'resumes_analyzed_week', 'resumes_analyzed_month',
        'total_revenue', 'revenue_today', 'revenue_week', 'revenue_month',
        'avg_response_time', 'error_rate', 'uptime_percentage', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('User Statistics', {
            'fields': (
                'total_users', 'active_users_today', 'active_users_week', 'active_users_month',
                'new_users_today', 'new_users_week', 'new_users_month'
            )
        }),
        ('Mentor Statistics', {
            'fields': ('total_mentors', 'active_mentors', 'pending_mentor_applications')
        }),
        ('Appointment Statistics', {
            'fields': (
                'total_appointments', 'appointments_today', 'appointments_week', 'appointments_month',
                'completed_appointments', 'cancelled_appointments'
            )
        }),
        ('Resume Statistics', {
            'fields': (
                'total_resumes', 'resumes_analyzed_today', 'resumes_analyzed_week', 'resumes_analyzed_month'
            )
        }),
        ('Revenue Statistics', {
            'fields': ('total_revenue', 'revenue_today', 'revenue_week', 'revenue_month')
        }),
        ('System Performance', {
            'fields': ('avg_response_time', 'error_rate', 'uptime_percentage')
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display = [
        'admin_user', 'action_type', 'action_description', 'target_model',
        'target_id', 'ip_address', 'created_at'
    ]
    list_filter = ['action_type', 'created_at', 'admin_user']
    search_fields = ['admin_user__username', 'action_description', 'target_model']
    readonly_fields = [
        'admin_user', 'action_type', 'action_description', 'target_model',
        'target_id', 'action_data', 'ip_address', 'user_agent', 'created_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('admin_user', 'action_type', 'action_description')
        }),
        ('Operation Details', {
            'fields': ('target_model', 'target_id', 'action_data')
        }),
        ('Access Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = [
        'key', 'config_type', 'is_active', 'is_sensitive', 'updated_by', 'updated_at'
    ]
    list_filter = ['config_type', 'is_active', 'is_sensitive', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'config_type', 'description')
        }),
        ('Configuration Value', {
            'fields': ('value', 'is_active', 'is_sensitive')
        }),
        ('Update Information', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Record updater when saving"""
        if change:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'export_type', 'format', 'status', 'requested_by',
        'record_count', 'file_size', 'created_at'
    ]
    list_filter = ['export_type', 'format', 'status', 'created_at']
    search_fields = ['name', 'requested_by__username']
    readonly_fields = [
        'status', 'file_path', 'file_size', 'record_count', 'error_message',
        'requested_by', 'created_at', 'started_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'export_type', 'format', 'requested_by')
        }),
        ('Filter Conditions', {
            'fields': ('date_from', 'date_to', 'filters'),
            'classes': ('collapse',)
        }),
        ('Status and Results', {
            'fields': ('status', 'file_path', 'file_size', 'record_count', 'error_message')
        }),
        ('Time Information', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='processing', started_at=timezone.now())
        self.message_user(request, f'{updated} exports marked as processing.')
    mark_as_processing.short_description = "Mark selected exports as processing"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} exports marked as completed.')
    mark_as_completed.short_description = "Mark selected exports as completed"
    
    def mark_as_failed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='failed', completed_at=timezone.now())
        self.message_user(request, f'{updated} exports marked as failed.')
    mark_as_failed.short_description = "Mark selected exports as failed"

@admin.register(ContentModeration)
class ContentModerationAdmin(admin.ModelAdmin):
    list_display = [
        'content_type', 'content_id', 'status', 'reviewed_by', 'created_at'
    ]
    list_filter = ['content_type', 'status', 'created_at', 'reviewed_by']
    search_fields = ['content_preview', 'flagged_reason']
    readonly_fields = [
        'content_type', 'content_id', 'content_preview', 'reviewed_by',
        'reviewed_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Content Information', {
            'fields': ('content_type', 'content_id', 'content_preview')
        }),
        ('Review Information', {
            'fields': ('status', 'flagged_reason', 'moderation_notes')
        }),
        ('Reviewer Information', {
            'fields': ('reviewed_by', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_content', 'reject_content', 'flag_content']
    
    def approve_content(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} content items approved.')
    approve_content.short_description = "Approve selected content"
    
    def reject_content(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} content items rejected.')
    reject_content.short_description = "Reject selected content"
    
    def flag_content(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status='flagged',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} content items flagged.')
    flag_content.short_description = "Flag selected content"
