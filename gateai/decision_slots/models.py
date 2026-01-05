from django.db import models
from django.utils import timezone


class ResourceLock(models.Model):
    """
    OS-level resource locking primitive.
    
    Domain-agnostic kernel model for managing temporary resource holds.
    Maps to Appointment records via resource_id (Day 1 transitional ABI).
    
    Future: Will support generic resource types via resource_type field.
    """
    
    # Core locking fields (OS ABI)
    resource_id = models.IntegerField(
        help_text="ID of locked resource (maps to Appointment PK)"
    )
    owner_id = models.IntegerField(
        help_text="ID of lock owner (User PK) - IntegerField for Day 1 safety"
    )
    expires_at = models.DateTimeField(
        help_text="Lock expiration timestamp (UTC)"
    )
    
    # State machine
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('released', 'Released'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'decision_slots_resourcelock'
        indexes = [
            models.Index(fields=['resource_id', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['owner_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Lock({self.resource_id}) by User({self.owner_id}) until {self.expires_at}"
    
    @property
    def is_expired(self):
        """Check if lock has expired"""
        return timezone.now() > self.expires_at
    
    def release(self):
        """Release the lock"""
        self.status = 'released'
        self.save(update_fields=['status', 'updated_at'])
