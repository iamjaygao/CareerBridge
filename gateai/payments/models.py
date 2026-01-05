from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class PaymentSettings(models.Model):
    """Global payment settings (platform defaults)"""

    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        help_text="Default platform fee percentage if service-specific not set"
    )
    allow_service_override = models.BooleanField(
        default=True,
        help_text="Allow MentorService.platform_fee_percentage to override global setting"
    )
    stripe_connect_enabled = models.BooleanField(
        default=True,
        help_text="Use Stripe Connect transfers when mentor has stripe_account_id"
    )
    payout_hold_days = models.PositiveSmallIntegerField(
        default=2,
        help_text="Hold period (days) after completion before payout is eligible"
    )
    payout_requires_admin_approval = models.BooleanField(
        default=False,
        help_text="Require admin approval before releasing payouts"
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment Settings"
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"Payment Settings (platform_fee={self.platform_fee_percentage}%)"

    def save(self, *args, **kwargs):
        # Enforce singleton: only one PaymentSettings row allowed
        if not self.pk and PaymentSettings.objects.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError("Only one PaymentSettings instance is allowed.")
        super().save(*args, **kwargs)

class Payment(models.Model):
    """Payment model for handling all payment transactions"""
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_PROVIDER_CHOICES = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('square', 'Square'),
    )
    
    PAYMENT_TYPE_CHOICES = (
        ('appointment', 'Appointment'),
        ('resume_analysis', 'Resume Analysis'),
        ('subscription', 'Subscription'),
        ('refund', 'Refund'),
    )
    PAYOUT_STATUS_CHOICES = (
        ('not_eligible', 'Not Eligible'),
        ('pending', 'Pending Hold/Approval'),
        ('ready', 'Ready to Pay Out'),
        ('paid', 'Paid Out'),
        ('failed', 'Payout Failed'),
        ('on_hold', 'On Hold'),
    )
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    mentor = models.ForeignKey('human_loop.MentorProfile', on_delete=models.CASCADE, null=True, blank=True, related_name='received_payments')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    
    # Payment details
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='appointment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDER_CHOICES)
    
    # Provider information
    provider_payment_id = models.CharField(max_length=100, blank=True)
    provider_refund_id = models.CharField(max_length=100, blank=True)
    
    # Fee breakdown
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mentor_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Payout tracking
    payout_status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS_CHOICES,
        default='not_eligible'
    )
    payout_available_at = models.DateTimeField(null=True, blank=True)
    payout_paid_at = models.DateTimeField(null=True, blank=True)
    payout_transfer_id = models.CharField(max_length=120, blank=True)
    payout_failure_reason = models.TextField(blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['provider', 'provider_payment_id']),
            models.Index(fields=['payment_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Calculate fees if not set
        if self.platform_fee == 0 and self.amount > 0:
            self.platform_fee = self.amount * Decimal('0.15')  # 15% platform fee
            self.mentor_earnings = self.amount - self.platform_fee
        
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_refundable(self):
        return self.status == 'completed' and not self.provider_refund_id
    
    @property
    def total_amount(self):
        return self.amount + self.tax_amount

class PaymentMethod(models.Model):
    """User's saved payment methods"""
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    provider = models.CharField(max_length=20)
    provider_token = models.CharField(max_length=255)  # Encrypted token
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Card information (masked)
    last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    expiry_month = models.CharField(max_length=2, blank=True)
    expiry_year = models.CharField(max_length=4, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['method_type', 'is_active']),
        ]
    
    def __str__(self):
        if self.method_type == 'card':
            return f"{self.user.username} - {self.card_brand} ****{self.last_four}"
        return f"{self.user.username} - {self.get_method_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default method per user
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class Refund(models.Model):
    """Refund model for tracking payment refunds"""
    
    REFUND_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    REFUND_REASON_CHOICES = (
        ('requested_by_customer', 'Requested by Customer'),
        ('duplicate', 'Duplicate'),
        ('fraudulent', 'Fraudulent'),
        ('requested_by_merchant', 'Requested by Merchant'),
        ('expired_uncaptured_charge', 'Expired Uncaptured Charge'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    reason = models.CharField(max_length=30, choices=REFUND_REASON_CHOICES)
    
    # Provider information
    provider_refund_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.id} - {self.payment.user.username} - {self.amount} {self.currency}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'

class PaymentWebhook(models.Model):
    """Model for tracking payment webhooks"""
    
    WEBHOOK_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )
    
    provider = models.CharField(max_length=20)
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=WEBHOOK_STATUS_CHOICES, default='pending')
    
    # Webhook data
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    
    # Processing information
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    error_message = models.TextField(blank=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['event_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.status}"
