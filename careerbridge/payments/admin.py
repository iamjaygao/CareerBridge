from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Payment, PaymentMethod, Refund, PaymentWebhook

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'payment_type', 'amount', 'currency', 'status', 
        'provider', 'is_completed', 'created_at'
    ]
    list_filter = [
        'status', 'payment_type', 'provider', 'currency', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'description', 
        'provider_payment_id', 'mentor__user__username'
    ]
    readonly_fields = [
        'platform_fee', 'mentor_earnings', 'is_completed', 'is_refundable',
        'total_amount', 'created_at', 'updated_at', 'paid_at', 'refunded_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'mentor', 'appointment', 'payment_type', 'provider')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'status', 'description')
        }),
        ('Provider Information', {
            'fields': ('provider_payment_id', 'provider_refund_id'),
            'classes': ('collapse',)
        }),
        ('Fee Breakdown', {
            'fields': ('platform_fee', 'mentor_earnings', 'tax_amount', 'total_amount')
        }),
        ('Status Information', {
            'fields': ('is_completed', 'is_refundable')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'refunded_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', paid_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_refunded(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='refunded', refunded_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as refunded.')
    mark_as_refunded.short_description = "Mark selected payments as refunded"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'mentor', 'mentor__user')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'method_type', 'provider', 'is_default', 'is_active',
        'card_display', 'created_at'
    ]
    list_filter = ['method_type', 'provider', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'last_four']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'method_type', 'provider', 'is_default', 'is_active')
        }),
        ('Card Information', {
            'fields': ('last_four', 'card_brand', 'expiry_month', 'expiry_year'),
            'classes': ('collapse',)
        }),
        ('Provider Information', {
            'fields': ('provider_token',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_methods', 'deactivate_methods']
    
    def card_display(self, obj):
        if obj.method_type == 'card' and obj.last_four:
            return f"{obj.card_brand} ****{obj.last_four}"
        return obj.get_method_type_display()
    card_display.short_description = "Card"
    
    def activate_methods(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} payment methods activated.')
    activate_methods.short_description = "Activate selected payment methods"
    
    def deactivate_methods(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} payment methods deactivated.')
    deactivate_methods.short_description = "Deactivate selected payment methods"

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'payment', 'amount', 'currency', 'status', 'reason',
        'is_completed', 'created_at'
    ]
    list_filter = ['status', 'reason', 'currency', 'created_at']
    search_fields = [
        'payment__user__username', 'payment__user__email', 
        'description', 'provider_refund_id'
    ]
    readonly_fields = [
        'is_completed', 'created_at', 'updated_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment', 'amount', 'currency', 'status', 'reason')
        }),
        ('Provider Information', {
            'fields': ('provider_refund_id',),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('description', 'is_completed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', processed_at=timezone.now())
        self.message_user(request, f'{updated} refunds marked as completed.')
    mark_as_completed.short_description = "Mark selected refunds as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} refunds marked as failed.')
    mark_as_failed.short_description = "Mark selected refunds as failed"

@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'provider', 'event_type', 'event_id', 'status',
        'processing_time_display', 'received_at'
    ]
    list_filter = ['provider', 'event_type', 'status', 'received_at']
    search_fields = ['event_id', 'event_type', 'error_message']
    readonly_fields = [
        'received_at', 'processed_at', 'processing_time_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'event_type', 'event_id', 'status')
        }),
        ('Processing Information', {
            'fields': ('processing_time', 'processing_time_display', 'error_message')
        }),
        ('Webhook Data', {
            'fields': ('payload', 'headers'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('received_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processed', 'mark_as_failed']
    
    def processing_time_display(self, obj):
        if obj.processing_time:
            return f"{obj.processing_time:.3f}s"
        return "N/A"
    processing_time_display.short_description = "Processing Time"
    
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='processed', processed_at=timezone.now())
        self.message_user(request, f'{updated} webhooks marked as processed.')
    mark_as_processed.short_description = "Mark selected webhooks as processed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} webhooks marked as failed.')
    mark_as_failed.short_description = "Mark selected webhooks as failed"

# Payment Statistics Admin
class PaymentStatisticsAdmin(admin.ModelAdmin):
    """Admin view for payment statistics"""
    
    def changelist_view(self, request, extra_context=None):
        # Calculate payment statistics
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Overall statistics
        total_payments = Payment.objects.count()
        total_amount = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        successful_payments = Payment.objects.filter(status='completed').count()
        failed_payments = Payment.objects.filter(status='failed').count()
        refunded_payments = Payment.objects.filter(status='refunded').count()
        
        # Time-based statistics
        payments_today = Payment.objects.filter(created_at__date=today).count()
        payments_this_week = Payment.objects.filter(created_at__date__gte=week_ago).count()
        payments_this_month = Payment.objects.filter(created_at__date__gte=month_ago).count()
        
        revenue_today = Payment.objects.filter(
            status='completed', created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_this_week = Payment.objects.filter(
            status='completed', created_at__date__gte=week_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_this_month = Payment.objects.filter(
            status='completed', created_at__date__gte=month_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Success rate
        success_rate = 0
        if total_payments > 0:
            success_rate = (successful_payments / total_payments) * 100
        
        # Average payment amount
        avg_payment = 0
        if successful_payments > 0:
            avg_payment = total_amount / successful_payments
        
        # Platform fees and mentor earnings
        platform_fees = Payment.objects.filter(status='completed').aggregate(
            total=Sum('platform_fee')
        )['total'] or 0
        
        mentor_earnings = Payment.objects.filter(status='completed').aggregate(
            total=Sum('mentor_earnings')
        )['total'] or 0
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_payments': total_payments,
            'total_amount': total_amount,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'refunded_payments': refunded_payments,
            'success_rate': round(success_rate, 2),
            'avg_payment': round(avg_payment, 2),
            'platform_fees': platform_fees,
            'mentor_earnings': mentor_earnings,
            'payments_today': payments_today,
            'payments_this_week': payments_this_week,
            'payments_this_month': payments_this_month,
            'revenue_today': revenue_today,
            'revenue_this_week': revenue_this_week,
            'revenue_this_month': revenue_this_month,
        })
        
        return super().changelist_view(request, extra_context)
