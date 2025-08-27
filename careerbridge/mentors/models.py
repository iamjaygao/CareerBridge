from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import time, timedelta, datetime

class MentorProfile(models.Model):
    """Mentor profile model"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    # Basic information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_profile')
    bio = models.TextField(max_length=500, help_text="Brief introduction about yourself")
    years_of_experience = models.PositiveIntegerField(default=0, help_text="Years of professional experience")
    current_position = models.CharField(max_length=200, help_text="Current job title and company")
    industry = models.CharField(max_length=100, help_text="Primary industry (e.g., Technology, Finance)")
    
    # Payment information
    stripe_account_id = models.CharField(max_length=100, blank=True, help_text="Stripe Connect account ID for payments")
    paypal_email = models.EmailField(blank=True, help_text="PayPal email for receiving payments")
    bank_account_info = models.JSONField(default=dict, blank=True, help_text="Bank account information for wire transfers")
    # Stripe Connect KYC / capabilities
    payouts_enabled = models.BooleanField(default=False, help_text="Stripe Connect payouts enabled")
    charges_enabled = models.BooleanField(default=False, help_text="Stripe Connect charges enabled")
    kyc_disabled_reason = models.CharField(max_length=255, blank=True, help_text="If disabled, Stripe reason")
    kyc_due_by = models.DateTimeField(null=True, blank=True, help_text="KYC requirements due by")
    stripe_capabilities = models.JSONField(default=dict, blank=True, help_text="Stripe capabilities snapshot")
    
    # Status and review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, help_text="Admin review notes")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='mentor_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total earnings from all sessions")
    total_sessions = models.PositiveIntegerField(default=0, help_text="Total completed sessions")
    
    # Verification and badges
    is_verified = models.BooleanField(default=False, help_text="Mentor verification status")
    verification_badge = models.CharField(max_length=50, blank=True, help_text="Verification badge type")
    specializations = models.JSONField(default=list, help_text="List of specializations")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.current_position}"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def ranking_score(self):
        """Calculate ranking score based on rating and sessions"""
        from decimal import Decimal
        return (self.average_rating * Decimal('0.7')) + (Decimal(str(min(self.total_sessions / 10, 5))) * Decimal('0.3'))

class MentorAvailability(models.Model):
    """Mentor availability model with 30-minute slots"""
    
    DAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(help_text="Start time (30-minute intervals)")
    end_time = models.TimeField(help_text="End time (30-minute intervals)")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['mentor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.mentor.user.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def get_available_slots(self, date):
        """Get available 30-minute slots for a specific date"""
        slots = []
        current_time = self.start_time
        
        while current_time < self.end_time:
            slot_end = (datetime.combine(date, current_time) + timedelta(minutes=30)).time()
            if slot_end <= self.end_time:
                slots.append({
                    'start': current_time,
                    'end': slot_end,
                    'is_available': not MentorSession.objects.filter(
                        mentor=self.mentor,
                        scheduled_date=date,
                        scheduled_time=current_time,
                        status__in=['confirmed', 'pending']
                    ).exists()
                })
            current_time = slot_end
        
        return slots

class MentorService(models.Model):
    """Mentor service model"""
    
    SERVICE_TYPE_CHOICES = (
        ('resume_review', 'Resume Review'),
        ('mock_interview', 'Mock Interview'),
        ('career_consultation', 'Career Consultation'),
    )
    
    PRICING_MODEL_CHOICES = (
        ('hourly', 'Hourly Rate'),
        ('fixed', 'Fixed Price'),
        ('package', 'Package Deal'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Service title")
    description = models.TextField(help_text="Service description")
    
    # Pricing information
    pricing_model = models.CharField(max_length=20, choices=PRICING_MODEL_CHOICES, default='hourly')
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Price per hour in USD")
    fixed_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Fixed price for the service")
    package_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Package price")
    package_sessions = models.PositiveIntegerField(default=1, help_text="Number of sessions in package")
    
    # Commission and fees
    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="Platform fee percentage")
    mentor_earnings_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=85.00, help_text="Mentor earnings percentage")
    
    # Session duration
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Session duration in minutes")
    
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['mentor', 'service_type']
        ordering = ['mentor', 'service_type']
    
    def __str__(self):
        return f"{self.mentor.user.username} - {self.get_service_type_display()}"
    
    @property
    def display_price(self):
        """Get the display price based on pricing model"""
        if self.pricing_model == 'hourly':
            return f"${self.price_per_hour}/hour"
        elif self.pricing_model == 'fixed':
            return f"${self.fixed_price}"
        elif self.pricing_model == 'package':
            return f"${self.package_price} for {self.package_sessions} sessions"
        return "Price not set"
    
    def calculate_mentor_earnings(self, total_amount):
        """Calculate mentor earnings after platform fee"""
        return total_amount * (self.mentor_earnings_percentage / 100)

class MentorSession(models.Model):
    """Mentor session/appointment model"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booked_sessions')
    service = models.ForeignKey(MentorService, on_delete=models.CASCADE, related_name='sessions')
    
    # Session details
    scheduled_date = models.DateField(help_text="Scheduled session date")
    scheduled_time = models.TimeField(help_text="Scheduled session time")
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Session duration")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Session notes
    user_notes = models.TextField(blank=True, help_text="User's notes for the session")
    mentor_notes = models.TextField(blank=True, help_text="Mentor's notes for the session")
    session_feedback = models.TextField(blank=True, help_text="Session feedback")
    
    # Meeting details
    meeting_link = models.URLField(blank=True, help_text="Video meeting link")
    meeting_platform = models.CharField(max_length=50, blank=True, help_text="Meeting platform (Zoom, Google Meet, etc.)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
    
    def __str__(self):
        return f"{self.mentor.user.username} - {self.user.username} - {self.scheduled_date} {self.scheduled_time}"
    
    @property
    def is_upcoming(self):
        """Check if session is upcoming"""
        now = timezone.now()
        session_datetime = timezone.make_aware(
            datetime.combine(self.scheduled_date, self.scheduled_time)
        )
        return session_datetime > now and self.status in ['pending', 'confirmed']
    
    def complete_session(self):
        """Mark session as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update mentor statistics
        self.mentor.total_sessions += 1
        self.mentor.save()

class MentorReview(models.Model):
    """Mentor review model"""
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_reviews_given')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(max_length=500, help_text="Review comment")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['mentor', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.mentor.user.username} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        # Update mentor's average rating after saving review
        super().save(*args, **kwargs)
        self.update_mentor_rating()
    
    def update_mentor_rating(self):
        """Update mentor's average rating"""
        reviews = MentorReview.objects.filter(mentor=self.mentor)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.mentor.average_rating = round(avg_rating, 2)
            self.mentor.total_reviews = reviews.count()
            self.mentor.save()

class MentorApplication(models.Model):
    """Mentor application model"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_applications')
    motivation = models.TextField(help_text="Why do you want to become a mentor?")
    relevant_experience = models.TextField(help_text="Describe your relevant experience")
    
    # Payment preferences
    preferred_payment_method = models.CharField(
        max_length=20, 
        choices=(
            ('stripe', 'Stripe Connect'),
            ('paypal', 'PayPal'),
            ('bank_transfer', 'Bank Transfer'),
        ),
        default='stripe',
        help_text="Preferred payment method"
    )
    
    # Review information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, help_text="Admin review notes")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='application_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
    
    def approve(self, reviewer):
        """Approve application and create mentor profile"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Create mentor profile
        MentorProfile.objects.create(
            user=self.user,
            bio=self.motivation,
            status='approved'
        )
    
    def reject(self, reviewer, notes=""):
        """Reject application"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

class MentorPayment(models.Model):
    """Mentor payment tracking model"""
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='payments')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='mentor_payments')
    
    # Payment amounts
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, help_text="Total amount paid by user")
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, help_text="Platform fee amount")
    mentor_earnings = models.DecimalField(max_digits=8, decimal_places=2, help_text="Amount mentor receives")
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Tax amount")
    
    # Payment processing
    payment_method = models.CharField(max_length=20, choices=(
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ))
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Payment processor transaction ID")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Refund information
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Refund amount")
    refund_reason = models.TextField(blank=True, help_text="Reason for refund")
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mentor.user.username} - ${self.mentor_earnings} - {self.get_payment_status_display()}"
    
    def process_payment(self):
        """Process the payment to mentor"""
        # This would integrate with payment processors
        # For now, just mark as completed
        self.payment_status = 'completed'
        self.processed_at = timezone.now()
        self.save()
        
        # Update mentor's total earnings
        self.mentor.total_earnings += self.mentor_earnings
        self.mentor.save()
    
    def process_refund(self, amount, reason=""):
        """Process refund for the payment"""
        self.refund_amount = amount
        self.refund_reason = reason
        self.refunded_at = timezone.now()
        self.payment_status = 'refunded'
        self.save()
        
        # Update mentor's total earnings
        self.mentor.total_earnings -= amount
        self.mentor.save()

class MentorNotification(models.Model):
    """Mentor notification model"""
    
    NOTIFICATION_TYPE_CHOICES = (
        ('session_booking', 'Session Booking'),
        ('session_reminder', 'Session Reminder'),
        ('session_cancellation', 'Session Cancellation'),
        ('payment_received', 'Payment Received'),
        ('review_received', 'Review Received'),
        ('application_update', 'Application Update'),
        ('system_announcement', 'System Announcement'),
    )
    
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message")
    
    # Notification status
    is_read = models.BooleanField(default=False, help_text="Whether notification has been read")
    is_sent = models.BooleanField(default=False, help_text="Whether email notification was sent")
    
    # Related objects
    related_session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, null=True, blank=True)
    related_payment = models.ForeignKey(MentorPayment, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mentor.user.username} - {self.notification_type} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
