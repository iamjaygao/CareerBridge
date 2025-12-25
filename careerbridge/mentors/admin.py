from django.contrib import admin
from .models import (
    MentorProfile, MentorService, MentorReview, MentorApplication, 
    MentorPayment, MentorAvailability, MentorSession, MentorNotification
)

@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'current_position', 'primary_track','system_role','industry', 'status',
        'is_verified', 'payouts_enabled', 'charges_enabled',
        'average_rating', 'total_reviews', 'total_sessions',
        'total_earnings', 'created_at',
    )
    list_filter = (
        'status', 'industry', 'years_of_experience',
        'is_verified', 'payouts_enabled', 'charges_enabled', 'created_at','primary_track',
    )
    search_fields = (
        'user__username', 'user__email',
        'current_position', 'industry','system_role',
    )
    readonly_fields = (
        'average_rating', 'total_reviews', 'total_sessions',
        'total_earnings', 'ranking_score', 'created_at', 'updated_at'
    )

    fieldsets = (
        ('SaaS Positioning (Core)', {
            'fields': (
                'primary_track',
                'system_role',
                'primary_focus',
                'session_focus',
            ),
            'description': 'Controls how this mentor appears in SaaS mentor cards',
        }),
        ('Basic Information', {
            'fields': ('user', 'bio', 'years_of_experience', 'current_position', 'industry', )
        }),
        ('Verification & Badges', {
            'fields': ('is_verified', 'verification_badge', 'specializations')
        }),
        ('Payment Information', {
            'fields': ('stripe_account_id', 'payouts_enabled', 'charges_enabled', 'kyc_disabled_reason', 'kyc_due_by', 'stripe_capabilities', 'paypal_email', 'bank_account_info'),
            'classes': ('collapse',)
        }),
        ('Status & Review', {
            'fields': ('status', 'review_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_reviews', 'total_sessions', 'total_earnings', 'ranking_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_mentors', 'unverify_mentors']
    
    def verify_mentors(self, request, queryset):
        for mentor in queryset:
            mentor.is_verified = True
            mentor.save()
        self.message_user(request, f"Verified {queryset.count()} mentors.")
    verify_mentors.short_description = "Verify selected mentors"
    
    def unverify_mentors(self, request, queryset):
        for mentor in queryset:
            mentor.is_verified = False
            mentor.save()
        self.message_user(request, f"Unverified {queryset.count()} mentors.")
    unverify_mentors.short_description = "Unverify selected mentors"

@admin.register(MentorAvailability)
class MentorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('mentor__user__username',)

@admin.register(MentorSession)
class MentorSessionAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'user', 'service', 'scheduled_date', 'scheduled_time', 'status', 'is_upcoming')
    list_filter = ('status', 'scheduled_date', 'created_at')
    search_fields = ('mentor__user__username', 'user__username', 'service__title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'is_upcoming')
    
    fieldsets = (
        ('Session Information', {
            'fields': ('mentor', 'user', 'service', 'scheduled_date', 'scheduled_time', 'duration_minutes', 'status')
        }),
        ('Session Details', {
            'fields': ('user_notes', 'mentor_notes', 'session_feedback')
        }),
        ('Meeting Information', {
            'fields': ('meeting_link', 'meeting_platform')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_sessions', 'complete_sessions', 'cancel_sessions']
    
    def confirm_sessions(self, request, queryset):
        for session in queryset.filter(status='pending'):
            session.status = 'confirmed'
            session.save()
        self.message_user(request, f"Confirmed {queryset.count()} sessions.")
    confirm_sessions.short_description = "Confirm selected sessions"
    
    def complete_sessions(self, request, queryset):
        for session in queryset.filter(status='confirmed'):
            session.complete_session()
        self.message_user(request, f"Completed {queryset.count()} sessions.")
    complete_sessions.short_description = "Complete selected sessions"
    
    def cancel_sessions(self, request, queryset):
        for session in queryset.filter(status__in=['pending', 'confirmed']):
            session.status = 'cancelled'
            session.save()
        self.message_user(request, f"Cancelled {queryset.count()} sessions.")
    cancel_sessions.short_description = "Cancel selected sessions"

@admin.register(MentorService)
class MentorServiceAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'service_type', 'title', 'pricing_model', 'display_price', 'duration_minutes', 'is_active')
    list_filter = ('service_type', 'pricing_model', 'is_active', 'created_at')
    search_fields = ('mentor__user__username', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Service Information', {
            'fields': ('mentor', 'service_type', 'title', 'description', 'duration_minutes', 'is_active')
        }),
        ('Pricing', {
            'fields': ('pricing_model', 'price_per_hour', 'fixed_price', 'package_price', 'package_sessions')
        }),
        ('Commission', {
            'fields': ('platform_fee_percentage', 'mentor_earnings_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MentorReview)
class MentorReviewAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'user', 'session', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('mentor__user__username', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'preferred_payment_method', 'reviewed_by', 'created_at', 'reviewed_at')
    list_filter = ('status', 'preferred_payment_method', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'user__email', 'motivation', 'relevant_experience')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('user', 'motivation', 'relevant_experience')
        }),
        ('Payment Preferences', {
            'fields': ('preferred_payment_method',)
        }),
        ('Review Information', {
            'fields': ('status', 'review_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} applications.")
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.reject(request.user)
        self.message_user(request, f"Rejected {queryset.count()} applications.")
    reject_applications.short_description = "Reject selected applications"

@admin.register(MentorPayment)
class MentorPaymentAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'session', 'total_amount', 'platform_fee', 'mentor_earnings', 'tax_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('mentor__user__username', 'transaction_id')
    readonly_fields = ('created_at', 'processed_at', 'refunded_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('mentor', 'session', 'total_amount', 'platform_fee', 'mentor_earnings', 'tax_amount')
        }),
        ('Processing', {
            'fields': ('payment_method', 'transaction_id', 'payment_status')
        }),
        ('Refund Information', {
            'fields': ('refund_amount', 'refund_reason', 'refunded_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['process_payments', 'process_refunds']
    
    def process_payments(self, request, queryset):
        for payment in queryset.filter(payment_status='pending'):
            payment.process_payment()
        self.message_user(request, f"Processed {queryset.count()} payments.")
    process_payments.short_description = "Process selected payments"
    
    def process_refunds(self, request, queryset):
        for payment in queryset.filter(payment_status='completed'):
            payment.process_refund(payment.total_amount, "Admin refund")
        self.message_user(request, f"Processed refunds for {queryset.count()} payments.")
    process_refunds.short_description = "Process refunds for selected payments"

@admin.register(MentorNotification)
class MentorNotificationAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'notification_type', 'title', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'created_at')
    search_fields = ('mentor__user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('mentor', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'read_at')
        }),
        ('Related Objects', {
            'fields': ('related_session', 'related_payment'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
        self.message_user(request, f"Marked {queryset.count()} notifications as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        for notification in queryset.filter(is_read=True):
            notification.is_read = False
            notification.read_at = None
            notification.save()
        self.message_user(request, f"Marked {queryset.count()} notifications as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def mark_as_sent(self, request, queryset):
        for notification in queryset.filter(is_sent=False):
            notification.is_sent = True
            notification.save()
        self.message_user(request, f"Marked {queryset.count()} notifications as sent.")
    mark_as_sent.short_description = "Mark selected notifications as sent"
