from django.contrib import admin
from .models import ResourceLock


@admin.register(ResourceLock)
class ResourceLockAdmin(admin.ModelAdmin):
    list_display = ('id', 'resource_id', 'owner_id', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('resource_id', 'owner_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Lock Information', {
            'fields': ('resource_id', 'owner_id', 'expires_at', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
