from django.db import models, transaction
from django.utils import timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ResourceLock(models.Model):
    """
    OS-level resource locking primitive.
    
    Domain-agnostic kernel model for managing temporary resource holds.
    Day 3: Enhanced with multi-resource support (resource_type, decision_id, resource_key).
    
    Supports:
    - Composite locks (multiple resources under one decision_id)
    - Partial rollback (release specific resource tuples)
    - Full rollback (release all locks for a decision_id)
    """
    
    # Resource type constants (flat strings, no FK)
    RESOURCE_TYPE_APPOINTMENT = "APPOINTMENT"
    RESOURCE_TYPE_STAGING_SERVER = "STAGING_SERVER"
    RESOURCE_TYPE_API_CREDENTIAL = "API_CREDENTIAL"
    
    RESOURCE_TYPE_CHOICES = [
        (RESOURCE_TYPE_APPOINTMENT, "Appointment"),
        (RESOURCE_TYPE_STAGING_SERVER, "Staging Server"),
        (RESOURCE_TYPE_API_CREDENTIAL, "API Credential"),
    ]
    
    # Core locking fields (OS ABI)
    decision_id = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Groups composite locks; allows full/partial rollback (NO static default; must be provided)"
    )
    resource_type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPE_CHOICES,
        default=RESOURCE_TYPE_APPOINTMENT,
        db_index=True,
        help_text="Type of locked resource (extensible)"
    )
    resource_id = models.IntegerField(
        help_text="ID of locked resource (domain-specific PK)"
    )
    resource_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional specificity key for composite locks"
    )
    owner_id = models.IntegerField(
        help_text="ID of lock owner (User PK)"
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
    
    objects = models.Manager()  # Explicit default manager
    
    class Meta:
        db_table = 'decision_slots_resourcelock'
        indexes = [
            models.Index(fields=['decision_id', 'status']),
            models.Index(fields=['resource_type', 'resource_id', 'status']),
            models.Index(fields=['expires_at', 'status']),
            models.Index(fields=['owner_id', 'status']),
        ]
        # Unique constraint on resource_type and resource_id
        constraints = [
            models.UniqueConstraint(
                fields=["resource_type", "resource_id"],
                name="uniq_physical_resource_lock",
            )
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Lock({self.resource_type}:{self.resource_id}) decision={self.decision_id} by User({self.owner_id})"
    
    @property
    def is_expired(self):
        """Check if lock has expired"""
        return timezone.now() > self.expires_at
    
    def release(self):
        """
        DEPRECATED: Use release_and_audit() instead for proper audit trail.
        
        Soft-releases the lock by updating status. Does not create audit entry.
        Prefer the class methods or release_and_audit() for new code.
        """
        self.status = 'released'
        self.save(update_fields=['status', 'updated_at'])
    
    def release_and_audit(self, reason: Optional[str] = None) -> bool:
        """
        Release this lock with audit trail (physical delete + audit log).
        
        Creates KernelAuditLog entry BEFORE deletion within same transaction.
        Uses physical delete to allow re-locking of the same resource tuple.
        
        Args:
            reason: Human-readable release reason
        
        Returns:
            True if released, False if lock was already released/missing
        """
        from kernel.models import KernelAuditLog
        from kernel.lock_primitives import compute_lock_release_audit
        
        with transaction.atomic():
            # Lock row for deletion (or detect if already gone)
            lock = ResourceLock.objects.select_for_update().filter(pk=self.pk).first()
            
            if not lock:
                return False  # Already released/deleted
            
            # Create audit entry BEFORE deletion
            audit_payload = compute_lock_release_audit(
                decision_id=lock.decision_id,
                resource_type=lock.resource_type,
                resource_id=lock.resource_id,
                resource_key=lock.resource_key,
                reason=reason,
            )
            
            KernelAuditLog.objects.create(
                event_type="RESOURCE_LOCK_RELEASED",
                decision_id=lock.decision_id,
                idempotency_key=f"lock_release:{lock.decision_id}:{lock.id}",
                context_hash="",  # Not tied to a kernel decision
                schema_version="1.0",
                payload=audit_payload,
                status=KernelAuditLog.STATUS_HANDLED,
            )
            
            # Physical delete to allow re-locking
            lock.delete()
            
            logger.info(
                "ResourceLock released with audit",
                extra={
                    "decision_id": lock.decision_id,
                    "resource_type": lock.resource_type,
                    "resource_id": lock.resource_id,
                    "reason": reason or "none",
                },
            )
            
            return True
    
    @classmethod
    def create_lock(cls, *, decision_id=None, resource_type, resource_id, resource_key=None, 
                    owner_id, expires_at, status='active'):
        """
        Safe creation helper that ensures decision_id is never 'legacy:0'.
        
        If decision_id is not provided, computes a deterministic value based on resource tuple.
        This helper is optional but recommended to prevent accidental legacy:0 writes.
        
        Safety guards:
        - Rejects decision_id='legacy:0'
        - Enforces max_length=128 constraint
        """
        if not decision_id:
            # Dynamic computation: ensure uniqueness per resource
            if resource_key:
                decision_id = f"auto:{resource_type}:{resource_id}:{resource_key}"
            else:
                decision_id = f"auto:{resource_type}:{resource_id}"
        
        # Guard 1: Never allow legacy:0
        if decision_id == "legacy:0":
            raise ValueError("decision_id='legacy:0' is prohibited for new locks")
        
        # Guard 2: Enforce max_length constraint (model field is max_length=128)
        if len(decision_id) > 128:
            raise ValueError(
                f"decision_id length ({len(decision_id)}) exceeds maximum allowed (128): {decision_id[:50]}..."
            )
        
        return cls.objects.create(
            decision_id=decision_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_key=resource_key,
            owner_id=owner_id,
            expires_at=expires_at,
            status=status
        )
    
    @classmethod
    def release_for_decision(cls, decision_id: str, reason: Optional[str] = None) -> int:
        """
        Release ALL locks for a decision_id (full rollback).
        
        Physical delete + audit trail for each lock.
        Transaction-safe with row locking.
        Idempotent - returns 0 if no locks found.
        
        Args:
            decision_id: Decision ID to release all locks for
            reason: Human-readable release reason
        
        Returns:
            Number of locks released (deleted)
        """
        from kernel.models import KernelAuditLog
        from kernel.lock_primitives import compute_lock_release_audit
        
        with transaction.atomic():
            # Lock all matching rows
            locks = list(
                cls.objects.select_for_update()
                .filter(decision_id=decision_id, status='active')
                .all()
            )
            
            if not locks:
                return 0  # Idempotent
            
            # Create audit entries BEFORE deletion
            audit_payload = compute_lock_release_audit(
                decision_id=decision_id,
                reason=reason,
            )
            
            for lock in locks:
                # Per-lock audit entry
                lock_audit_payload = {
                    **audit_payload,
                    "resource_type": lock.resource_type,
                    "resource_id": str(lock.resource_id),
                }
                if lock.resource_key:
                    lock_audit_payload["resource_key"] = lock.resource_key
                
                KernelAuditLog.objects.create(
                    event_type="RESOURCE_LOCK_RELEASED",
                    decision_id=lock.decision_id,
                    idempotency_key=f"lock_release:{lock.decision_id}:{lock.id}",
                    context_hash="",
                    schema_version="1.0",
                    payload=lock_audit_payload,
                    status=KernelAuditLog.STATUS_HANDLED,
                )
            
            # Physical delete all locks
            count = cls.objects.filter(decision_id=decision_id, status='active').delete()[0]
            
            logger.info(
                "Full rollback: released all locks for decision",
                extra={
                    "decision_id": decision_id,
                    "count": count,
                    "reason": reason or "none",
                },
            )
            
            return count
    
    @classmethod
    def release_specific(
        cls,
        decision_id: str,
        resource_type: str,
        resource_id: int,
        resource_key: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Release a specific lock (partial rollback).
        
        Physical delete + audit trail.
        Transaction-safe with row locking.
        Idempotent - returns False if lock not found.
        
        Args:
            decision_id: Decision ID grouping the lock
            resource_type: Type of resource to release
            resource_id: ID of resource to release
            resource_key: Optional key for composite locks
            reason: Human-readable release reason
        
        Returns:
            True if lock was released, False if not found (idempotent)
        """
        from kernel.models import KernelAuditLog
        from kernel.lock_primitives import compute_lock_release_audit
        
        with transaction.atomic():
            # Lock specific row
            query = cls.objects.select_for_update().filter(
                decision_id=decision_id,
                resource_type=resource_type,
                resource_id=resource_id,
                status='active',
            )
            
            if resource_key is not None:
                query = query.filter(resource_key=resource_key)
            
            lock = query.first()
            
            if not lock:
                return False  # Idempotent
            
            # Create audit entry BEFORE deletion
            audit_payload = compute_lock_release_audit(
                decision_id=decision_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_key=resource_key,
                reason=reason,
            )
            
            KernelAuditLog.objects.create(
                event_type="RESOURCE_LOCK_RELEASED",
                decision_id=lock.decision_id,
                idempotency_key=f"lock_release:{lock.decision_id}:{lock.id}",
                context_hash="",
                schema_version="1.0",
                payload=audit_payload,
                status=KernelAuditLog.STATUS_HANDLED,
            )
            
            # Physical delete
            lock.delete()
            
            logger.info(
                "Partial rollback: released specific lock",
                extra={
                    "decision_id": decision_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "resource_key": resource_key,
                    "reason": reason or "none",
                },
            )
            
            return True
