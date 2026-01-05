from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta

class TimeSlot(models.Model):
    """Mentor available time slot"""
    
    mentor = models.ForeignKey('human_loop.MentorProfile', on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField(help_text="Start time")
    end_time = models.DateTimeField(help_text="End time")
    is_available = models.BooleanField(default=True, help_text="Whether available")
    is_recurring = models.BooleanField(default=False, help_text="Whether recurring time")
    recurring_pattern = models.CharField(max_length=50, blank=True, help_text="Recurring pattern (weekly, monthly)")
    
    # Booking limits
    max_bookings = models.PositiveIntegerField(default=1, help_text="Maximum bookings")
    current_bookings = models.PositiveIntegerField(default=0, help_text="Current bookings")
    
    # Pricing settings
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Price")
    currency = models.CharField(max_length=3, default='USD', help_text="Currency")
    
    # Hold fields
    reserved_until = models.DateTimeField(null=True, blank=True)
    reserved_appointment = models.ForeignKey(
        "Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reserved_slot",
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'decision_slots_timeslot'  # Preserve existing table
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['mentor', 'start_time']),
            models.Index(fields=['is_available', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.mentor.user.get_full_name()} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_bookable(self):
        """Check if bookable"""
        return (
            self.is_available and
            self.current_bookings < self.max_bookings and
            self.start_time > timezone.now()
        )
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

class Appointment(models.Model):
    """Appointment record"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('expired', 'Expired'),
    )
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    mentor = models.ForeignKey('human_loop.MentorProfile', on_delete=models.CASCADE, related_name='appointments')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(
        'human_loop.MentorService',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
    )
    
    # Appointment details
    title = models.CharField(max_length=200, help_text="Appointment title")
    description = models.TextField(blank=True, help_text="Appointment description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Time information
    scheduled_start = models.DateTimeField(help_text="Scheduled start time")
    scheduled_end = models.DateTimeField(help_text="Scheduled end time")
    actual_start = models.DateTimeField(null=True, blank=True, help_text="Actual start time")
    actual_end = models.DateTimeField(null=True, blank=True, help_text="Actual end time")
    
    # Pricing and payment
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Appointment price")
    currency = models.CharField(max_length=3, default='USD', help_text="Currency")
    is_paid = models.BooleanField(default=False, help_text="Whether paid")
    payment_method = models.CharField(max_length=50, blank=True, help_text="Payment method")
    
    # Meeting information
    meeting_link = models.URLField(blank=True, help_text="Meeting link")
    meeting_platform = models.CharField(max_length=50, blank=True, help_text="Meeting platform")
    meeting_notes = models.TextField(blank=True, help_text="Meeting notes")
    
    # Rating and feedback
    user_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True, help_text="User rating (1-5)"
    )
    user_feedback = models.TextField(blank=True, help_text="User feedback")
    mentor_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True, help_text="Mentor rating (1-5)"
    )
    mentor_feedback = models.TextField(blank=True, help_text="Mentor feedback")
    
    # Cancellation and refund
    cancellation_reason = models.TextField(blank=True, help_text="Cancellation reason")
    cancelled_by = models.CharField(max_length=20, blank=True, help_text="Cancelled by (user/mentor/system)")
    cancellation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Cancellation fee")
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Refund amount")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'decision_slots_appointment'  # Preserve existing table
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['mentor', 'status']),
            models.Index(fields=['scheduled_start']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.mentor.user.get_full_name()} - {self.scheduled_start.strftime('%Y-%m-%d %H:%M')}"

    def get_service_label(self) -> str:
        if self.service and getattr(self.service, "title", ""):
            return self.service.title
        if self.title:
            return self.title
        return "Session"

    def get_scheduled_label(self) -> str:
        if not self.scheduled_start:
            return ""
        return self.scheduled_start.strftime("%Y-%m-%d %H:%M")

    def get_notification_details(self) -> str:
        service_label = self.get_service_label()
        scheduled_label = self.get_scheduled_label()
        if scheduled_label:
            return f"{service_label} on {scheduled_label}"
        return service_label

    def get_notification_payload(self) -> dict:
        mentor_name = ''
        if self.mentor and self.mentor.user:
            mentor_name = self.mentor.user.get_full_name() or self.mentor.user.username or ''
        student_name = ''
        if self.user:
            student_name = self.user.get_full_name() or self.user.username or ''

        return {
            'appointment_id': self.id,
            'appointment_details': self.get_notification_details(),
            'service_id': self.service_id,
            'service_title': self.get_service_label(),
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'mentor_id': self.mentor_id,
            'mentor_name': mentor_name,
            'student_id': self.user_id,
            'student_name': student_name,
        }
    
    @property
    def is_upcoming(self):
        """Check if the appointment is upcoming"""
        return self.scheduled_start > timezone.now() and self.status in ['pending', 'confirmed']
    
    @property
    def is_past(self):
        """Check if the appointment is in the past"""
        return self.scheduled_end < timezone.now()
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes"""
        if self.scheduled_start and self.scheduled_end:
            return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)
        return 0
    
    @property
    def can_cancel(self):
        """Check if the appointment can be cancelled"""
        return (
            self.status in ['pending', 'confirmed'] and
            self.scheduled_start > timezone.now() + timedelta(hours=24)
        )
    
    def cancel_appointment(self, reason="", cancelled_by="user"):
        """Cancel the appointment"""
        if not self.can_cancel:
            raise ValueError("Cannot cancel this appointment")
        
        self.status = 'cancelled'
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by
        self.save()
        
        # Release the time slot
        self.time_slot.current_bookings -= 1
        self.time_slot.save()

class AppointmentRequest(models.Model):
    """Appointment request (for mentor confirmation)"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointment_requests')
    mentor = models.ForeignKey('human_loop.MentorProfile', on_delete=models.CASCADE, related_name='appointment_requests')
    
    # Request details
    preferred_date = models.DateField(help_text="Preferred date")
    preferred_time_start = models.TimeField(help_text="Preferred start time")
    preferred_time_end = models.TimeField(help_text="Preferred end time")
    alternative_dates = models.JSONField(default=list, help_text="Alternative dates")
    
    # Appointment content
    title = models.CharField(max_length=200, help_text="Appointment title")
    description = models.TextField(help_text="Appointment description")
    topics = models.JSONField(default=list, help_text="Discussion topics")
    
    # Status and response
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mentor_response = models.TextField(blank=True, help_text="Mentor response")
    suggested_time_slots = models.JSONField(default=list, help_text="Mentor suggested time slots")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="Request expiration time")
    
    class Meta:
        db_table = 'decision_slots_appointmentrequest'  # Preserve existing table
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.mentor.user.get_full_name()} - {self.status}"
    
    @property
    def is_expired(self):
        """Check if the request is expired"""
        return timezone.now() > self.expires_at
