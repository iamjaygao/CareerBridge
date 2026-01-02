from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta, datetime


class MentorProfile(models.Model):
    """Mentor profile model"""

    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    PRIMARY_TRACK_CHOICES = (
        ('resume_review', 'Resume Review'),
        ('mock_interview', 'Mock Interview'),
        ('career_switch', 'Career Switch'),
        ('advanced_interview', 'Advanced Interview'),
    )


    primary_track = models.CharField(
        max_length=50,
        choices=PRIMARY_TRACK_CHOICES,
        blank=True,
        default="",
        help_text="Primary product track this mentor belongs to"
    )


    # Basic information
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_profile',
        limit_choices_to={'role': 'mentor'}
    )
    bio = models.TextField(max_length=500, help_text="Brief introduction about yourself")
    years_of_experience = models.PositiveIntegerField(default=0, help_text="Years of professional experience")
    current_position = models.CharField(max_length=200, help_text="Current job title and company")
    industry = models.CharField(max_length=100, help_text="Primary industry (e.g., Technology, Finance)")
    headline = models.CharField(
        max_length=255,
        blank=True,
        help_text="A short headline"
    )
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Starting price, pre-filled or auto-updated by Seed script"
    )
    
    primary_focus = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary problem this mentor helps with (shown on mentor cards)"
    )

    session_focus = models.CharField(
        max_length=150,
        blank=True,
        help_text="One-line session experience summary (shown on mentor cards)"
    )
    system_role = models.CharField(
        max_length=100,
        blank=True,
        help_text="System-level role, e.g. Senior System Design Reviewer"
    )



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
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total earnings from all sessions"
    )
    total_sessions = models.PositiveIntegerField(default=0, help_text="Total completed sessions")

    # Verification and badges
    is_verified = models.BooleanField(default=False, help_text="Mentor verification status")
    verification_badge = models.CharField(max_length=50, blank=True, help_text="Verification badge type")
    specializations = models.JSONField(default=list, help_text="List of specializations")
    
    # Primary service selection
    primary_service_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Mentor-selected primary service (SKU anchor)"
    )

    timezone = models.CharField(
        max_length=64,
        default=settings.TIME_ZONE,
        help_text="IANA timezone for availability (e.g., America/New_York)"
    )

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
        return (self.average_rating * Decimal('0.7')) + (
            Decimal(str(min(self.total_sessions / 10, 5))) * Decimal('0.3')
        )


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
    deliverables = models.JSONField(default=list, blank=True, help_text="List of items delivered in this service")

    pricing_model = models.CharField(max_length=20, choices=PRICING_MODEL_CHOICES, default='hourly')
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fixed_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    package_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    package_sessions = models.PositiveIntegerField(default=1)

    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    mentor_earnings_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=85.00)

    duration_minutes = models.PositiveIntegerField(default=60)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['mentor', 'service_type']
        ordering = ['mentor', 'service_type']

    def __str__(self):
        return f"{self.mentor.user.username} - {self.get_service_type_display()}"

    @property
    def display_price(self):
        if self.pricing_model == 'hourly':
            return f"${self.price_per_hour}/hour"
        elif self.pricing_model == 'fixed':
            return f"${self.fixed_price}"
        elif self.pricing_model == 'package':
            return f"${self.package_price} for {self.package_sessions} sessions"
        return "Price not set"

    def calculate_mentor_earnings(self, total_amount):
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

    scheduled_date = models.DateField(help_text="Scheduled session date")
    scheduled_time = models.TimeField(help_text="Scheduled session time")
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    user_notes = models.TextField(blank=True)
    mentor_notes = models.TextField(blank=True)
    session_feedback = models.TextField(blank=True)

    meeting_link = models.URLField(blank=True)
    meeting_platform = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']

    @property
    def is_upcoming(self):
        now = timezone.now()
        session_datetime = timezone.make_aware(
            datetime.combine(self.scheduled_date, self.scheduled_time)
        )
        return session_datetime > now and self.status in ['pending', 'confirmed']

    def complete_session(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        self.mentor.total_sessions += 1
        self.mentor.save()


class MentorReview(models.Model):
    """Mentor review model"""

    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_reviews_given')
    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['mentor', 'user']
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_mentor_rating()

    def update_mentor_rating(self):
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
    motivation = models.TextField()
    relevant_experience = models.TextField()

    preferred_payment_method = models.CharField(
        max_length=20,
        choices=(
            ('stripe', 'Stripe Connect'),
            ('paypal', 'PayPal'),
            ('bank_transfer', 'Bank Transfer'),
        ),
        default='stripe'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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

    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2)
    mentor_earnings = models.DecimalField(max_digits=8, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    payment_method = models.CharField(
        max_length=20,
        choices=(
            ('stripe', 'Stripe'),
            ('paypal', 'PayPal'),
            ('bank_transfer', 'Bank Transfer'),
        )
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def process_payment(self):
        self.payment_status = 'completed'
        self.processed_at = timezone.now()
        self.save()

        self.mentor.total_earnings += self.mentor_earnings
        self.mentor.save()

    def process_refund(self, amount, reason=""):
        self.refund_amount = amount
        self.refund_reason = reason
        self.refunded_at = timezone.now()
        self.payment_status = 'refunded'
        self.save()

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
    title = models.CharField(max_length=200)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    related_session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, null=True, blank=True)
    related_payment = models.ForeignKey(MentorPayment, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class HumanReviewTask(models.Model):
    """
    Human review task model for critical ATS signals.
    
    Created when a critical ATS signal is generated, requiring human review.
    Links signals to human reviewers (mentors/admins) for expert evaluation.
    """
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('assigned', 'Assigned to Reviewer'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    # Signal reference (Rule 15: SIGNAL INTEGRITY)
    signal = models.ForeignKey(
        'ats_signals.ATSSignal',
        on_delete=models.CASCADE,
        related_name='review_tasks',
        help_text="ATS Signal that triggered this review task"
    )
    decision_slot_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="DecisionSlot ID anchoring this review task (Rule 15)"
    )
    
    # Task metadata
    task_type = models.CharField(
        max_length=50,
        default='signal_review',
        help_text="Type of review task"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the review task"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='high',
        help_text="Priority level of the review task"
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_review_tasks',
        help_text="User (mentor/admin) assigned to review this task"
    )
    assigned_at = models.DateTimeField(null=True, blank=True, help_text="When task was assigned")
    
    # Review details
    review_notes = models.TextField(blank=True, help_text="Reviewer's notes and feedback")
    review_decision = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reviewer's decision (e.g., 'resolved', 'requires_action', 'false_positive')"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When review was completed")
    
    # Context information
    context_data = models.JSONField(
        default=dict,
        help_text="Additional context data for the review (resume_id, user_id, etc.)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this task should be completed"
    )
    
    class Meta:
        db_table = 'human_review_tasks'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['decision_slot_id']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['signal', 'status']),
        ]
        verbose_name = "Human Review Task"
        verbose_name_plural = "Human Review Tasks"
    
    def __str__(self):
        return f"Review Task {self.id} - {self.signal.signal_type} ({self.status})"
    
    @property
    def is_critical(self):
        """Check if task is for a critical signal."""
        return self.signal.severity == 'critical'
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_at:
            return False
        return timezone.now() > self.due_at and self.status not in ('completed', 'cancelled')
    
    def assign_to(self, reviewer):
        """Assign task to a reviewer."""
        self.assigned_to = reviewer
        self.status = 'assigned'
        self.assigned_at = timezone.now()
        self.save()
    
    def start_review(self):
        """Mark task as in progress."""
        if not self.assigned_to:
            raise ValueError("Task must be assigned before starting review")
        self.status = 'in_progress'
        self.save()
    
    def complete_review(self, decision: str, notes: str = ""):
        """Complete the review task."""
        self.status = 'completed'
        self.review_decision = decision
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
