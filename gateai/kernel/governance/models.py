"""
Kernel Governance Models

These models provide platform-level controls for feature flags, workload management,
and module activation/freezing with full audit trail.

GOVERNANCE POWER CONSTITUTION:
- Only SuperAdmin (is_superuser=True) can modify PlatformState and FeatureFlags
- Staff (is_staff=True, is_superuser=False) CANNOT modify governance settings
- BETA features are visible ONLY to superuser
- All changes must create GovernanceAudit records
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class PlatformState(models.Model):
    """
    Singleton-ish model representing the current platform governance state.
    
    Only ONE active record should exist. Updates increment governance_version
    to invalidate middleware cache.
    """
    
    STATE_CHOICES = [
        ('SINGLE_WORKLOAD', 'Single Workload Mode'),
        ('MULTI_WORKLOAD', 'Multi Workload Mode'),
        ('MAINTENANCE', 'Maintenance Mode'),
        ('MIGRATION', 'Migration Mode'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(
        max_length=50,
        choices=STATE_CHOICES,
        default='SINGLE_WORKLOAD',
        help_text='Current platform operating state'
    )
    active_workloads = models.JSONField(
        default=list,
        help_text='List of currently active workload identifiers (e.g., ["PEER_MOCK"])'
    )
    frozen_modules = models.JSONField(
        default=list,
        help_text='List of frozen module identifiers that return 404'
    )
    governance_version = models.PositiveIntegerField(
        default=1,
        help_text='Incremented on every change to invalidate middleware cache'
    )
    reason = models.TextField(
        help_text='Reason for the current state configuration'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='platform_state_updates',
        help_text='SuperAdmin who last updated this state'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Platform State'
        verbose_name_plural = 'Platform State'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'Platform State: {self.state} (v{self.governance_version})'
    
    def save(self, *args, **kwargs):
        """Increment governance_version on every save to invalidate cache"""
        if self.pk:
            self.governance_version += 1
        super().save(*args, **kwargs)


class FeatureFlag(models.Model):
    """
    Individual feature flag for controlling module/workload visibility and access.
    
    Each flag represents a specific module or feature that can be toggled ON/OFF/BETA.
    """
    
    STATE_CHOICES = [
        ('OFF', 'Disabled (404)'),
        ('BETA', 'Beta (SuperAdmin Only)'),
        ('ON', 'Enabled'),
    ]
    
    VISIBILITY_CHOICES = [
        ('internal', 'Internal Only'),
        ('staff', 'Staff Access'),
        ('user', 'User Access'),
        ('public', 'Public Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Unique feature key (e.g., PEER_MOCK, MENTORS, PAYMENTS)'
    )
    state = models.CharField(
        max_length=10,
        choices=STATE_CHOICES,
        default='OFF',
        help_text='Current state of this feature'
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='internal',
        help_text='Who can see this feature'
    )
    rollout_rule = models.JSONField(
        default=dict,
        blank=True,
        help_text='Rollout rules (e.g., percentage, user whitelist)'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for current state'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='feature_flag_updates',
        help_text='SuperAdmin who last updated this flag'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        ordering = ['key']
    
    def __str__(self):
        return f'{self.key}: {self.state}'
    
    def is_enabled_for_user(self, user):
        """
        Check if this feature is enabled for a given user.
        
        Rules:
        - OFF: Nobody can access
        - BETA: Only superusers can access
        - ON: Access based on visibility and rollout rules
        """
        if self.state == 'OFF':
            return False
        
        if self.state == 'BETA':
            return user and user.is_superuser
        
        if self.state == 'ON':
            # Check visibility requirements
            if self.visibility == 'public':
                return True
            if self.visibility == 'user' and user and user.is_authenticated:
                return True
            if self.visibility == 'staff' and user and user.is_staff:
                return True
            if self.visibility == 'internal' and user and user.is_superuser:
                return True
        
        return False


class GovernanceAudit(models.Model):
    """
    Audit log for all governance changes.
    
    Every change to PlatformState or FeatureFlag must create an audit entry.
    Tracks world context for 4-World OS Architecture.
    """
    
    ACTION_CHOICES = [
        ('PLATFORM_STATE_UPDATE', 'Platform State Updated'),
        ('FEATURE_FLAG_CREATE', 'Feature Flag Created'),
        ('FEATURE_FLAG_UPDATE', 'Feature Flag Updated'),
        ('GOVERNANCE_INIT', 'Governance Initialized'),
        ('WORKLOAD_ACTIVATE', 'Workload Activated'),
        ('WORKLOAD_FREEZE', 'Workload Frozen'),
        ('MODULE_ENABLE', 'Module Enabled'),
        ('MODULE_DISABLE', 'Module Disabled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='Type of governance action performed'
    )
    payload = models.JSONField(
        default=dict,
        help_text='Details of the change (before/after state, affected keys, etc.)'
    )
    reason = models.TextField(
        help_text='Reason for this action (required for all changes)'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='governance_actions',
        help_text='User who performed this action'
    )
    world = models.CharField(
        max_length=20, 
        blank=True, 
        default='kernel', 
        help_text="OS world: public, app, admin, or kernel"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Governance Audit'
        verbose_name_plural = 'Governance Audit Log'
        ordering = ['-created_at']
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f'{self.action} by {actor_name} at {self.created_at}'
