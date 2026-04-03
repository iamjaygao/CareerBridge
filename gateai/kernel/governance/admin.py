"""
Django Admin configuration for Governance models.

GOVERNANCE POWER CONSTITUTION:
- Only SuperAdmin (is_superuser=True) can modify PlatformState and FeatureFlags
- Staff (is_staff=True, is_superuser=False) get READ-ONLY access for visibility
- has_change_permission returns is_superuser for all write operations
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import PlatformState, FeatureFlag, GovernanceAudit


@admin.register(PlatformState)
class PlatformStateAdmin(admin.ModelAdmin):
    """
    Admin interface for PlatformState.
    
    Only SuperAdmins can modify. Staff can view for observability.
    """
    
    list_display = ['state', 'governance_version', 'updated_by', 'updated_at', 'reason_preview']
    list_filter = ['state', 'updated_at']
    search_fields = ['reason']
    readonly_fields = ['governance_version', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Platform Configuration', {
            'fields': ('state', 'active_workloads', 'frozen_modules', 'reason')
        }),
        ('Metadata', {
            'fields': ('governance_version', 'updated_by', 'updated_at', 'created_at')
        }),
    ]
    
    def reason_preview(self, obj):
        """Truncated reason for list view"""
        if len(obj.reason) > 50:
            return obj.reason[:50] + '...'
        return obj.reason
    reason_preview.short_description = 'Reason'
    
    def has_add_permission(self, request):
        """Only superusers can add (though typically only one exists)"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can modify"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete"""
        return request.user.is_superuser
    
    def has_module_permission(self, request):
        """Staff can view module, but only superusers can modify"""
        return request.user.is_staff


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """
    Admin interface for FeatureFlag.
    
    Only SuperAdmins can modify. Staff can view for observability.
    """
    
    list_display = ['key', 'state_badge', 'visibility', 'updated_by', 'updated_at', 'reason_preview']
    list_filter = ['state', 'visibility', 'updated_at']
    search_fields = ['key', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['key']
    
    fieldsets = [
        ('Feature Configuration', {
            'fields': ('key', 'state', 'visibility', 'rollout_rule', 'reason')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'updated_at', 'created_at')
        }),
    ]
    
    def state_badge(self, obj):
        """Colored badge for state"""
        colors = {
            'OFF': 'red',
            'BETA': 'orange',
            'ON': 'green',
        }
        color = colors.get(obj.state, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.state
        )
    state_badge.short_description = 'State'
    
    def reason_preview(self, obj):
        """Truncated reason for list view"""
        if not obj.reason:
            return '-'
        if len(obj.reason) > 50:
            return obj.reason[:50] + '...'
        return obj.reason
    reason_preview.short_description = 'Reason'
    
    def has_add_permission(self, request):
        """Only superusers can add feature flags"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can modify feature flags"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete feature flags"""
        return request.user.is_superuser
    
    def has_module_permission(self, request):
        """Staff can view module, but only superusers can modify"""
        return request.user.is_staff


@admin.register(GovernanceAudit)
class GovernanceAuditAdmin(admin.ModelAdmin):
    """
    Admin interface for GovernanceAudit (read-only).
    
    Audit logs are read-only for all users. They are created automatically
    by governance operations and should never be manually modified.
    """
    
    list_display = ['action', 'actor_name', 'created_at', 'reason_preview']
    list_filter = ['action', 'created_at']
    search_fields = ['reason', 'actor__username', 'actor__email']
    readonly_fields = ['action', 'payload', 'reason', 'actor', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = [
        ('Audit Information', {
            'fields': ('action', 'payload', 'reason', 'actor', 'created_at')
        }),
    ]
    
    def actor_name(self, obj):
        """Display actor username or 'System'"""
        return obj.actor.username if obj.actor else 'System'
    actor_name.short_description = 'Actor'
    
    def reason_preview(self, obj):
        """Truncated reason for list view"""
        if len(obj.reason) > 60:
            return obj.reason[:60] + '...'
        return obj.reason
    reason_preview.short_description = 'Reason'
    
    def has_add_permission(self, request):
        """Nobody can manually add audit entries"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Nobody can modify audit entries"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit entries (for cleanup)"""
        return request.user.is_superuser
    
    def has_module_permission(self, request):
        """Staff can view audit logs"""
        return request.user.is_staff
