from django.contrib import admin
from .models import TimeSlot, Appointment, AppointmentRequest

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'start_time', 'end_time', 'is_available', 'current_bookings', 'max_bookings', 'price']
    list_filter = ['is_available', 'is_recurring', 'currency', 'start_time']
    search_fields = ['mentor__name', 'mentor__user__username']
    readonly_fields = ['current_bookings', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('mentor', 'start_time', 'end_time', 'is_available')
        }),
        ('Booking Settings', {
            'fields': ('max_bookings', 'current_bookings', 'is_recurring', 'recurring_pattern')
        }),
        ('Pricing Settings', {
            'fields': ('price', 'currency')
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'mentor', 'title', 'status', 'scheduled_start', 'price', 'is_paid']
    list_filter = ['status', 'is_paid', 'currency', 'scheduled_start', 'created_at']
    search_fields = ['user__username', 'mentor__name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'mentor', 'time_slot', 'title', 'description', 'status')
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
        }),
        ('Payment Information', {
            'fields': ('price', 'currency', 'is_paid', 'payment_method')
        }),
        ('Meeting Information', {
            'fields': ('meeting_link', 'meeting_platform', 'meeting_notes')
        }),
        ('Rating and Feedback', {
            'fields': ('user_rating', 'user_feedback', 'mentor_rating', 'mentor_feedback')
        }),
        ('Cancellation Information', {
            'fields': ('cancellation_reason', 'cancelled_by', 'cancellation_fee', 'refund_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')
    mark_as_completed.short_description = "Mark selected appointments as completed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointments marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected appointments as cancelled"

@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'mentor', 'title', 'status', 'preferred_date', 'created_at']
    list_filter = ['status', 'preferred_date', 'created_at']
    search_fields = ['user__username', 'mentor__name', 'title']
    readonly_fields = ['created_at', 'updated_at', 'expires_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'mentor', 'title', 'description', 'topics', 'status')
        }),
        ('Time Preferences', {
            'fields': ('preferred_date', 'preferred_time_start', 'preferred_time_end', 'alternative_dates')
        }),
        ('Mentor Response', {
            'fields': ('mentor_response', 'suggested_time_slots')
        }),
        ('Time Information', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_accepted', 'mark_as_rejected']
    
    def mark_as_accepted(self, request, queryset):
        updated = queryset.update(status='accepted')
        self.message_user(request, f'{updated} requests marked as accepted.')
    mark_as_accepted.short_description = "Mark selected requests as accepted"
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} requests marked as rejected.')
    mark_as_rejected.short_description = "Mark selected requests as rejected"
