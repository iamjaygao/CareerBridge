import uuid

from django.db import models


class KernelAuditLog(models.Model):
    """
    Kernel-level audit and idempotency ledger.

    Records every kernel event emission and listener handling outcome.
    Day 3: Enhanced with telemetry fields for latency tracking and congestion detection.
    """

    STATUS_EMITTED = "EMITTED"
    STATUS_HANDLED = "HANDLED"
    STATUS_FAILED = "FAILED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = (
        (STATUS_EMITTED, "Emitted"),
        (STATUS_HANDLED, "Handled"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REJECTED, "Rejected"),
    )
    
    # Terminal states - no transitions allowed FROM these states
    TERMINAL_STATES = {STATUS_HANDLED, STATUS_REJECTED}

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=128)
    decision_id = models.CharField(max_length=128)
    idempotency_key = models.CharField(max_length=128, db_index=True)
    context_hash = models.CharField(max_length=128)
    schema_version = models.CharField(max_length=10, default="1.0")
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_EMITTED, db_index=True
    )
    failure_reason = models.TextField(blank=True)
    
    # Timestamps and telemetry (Day 3)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    handled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    latency_ms = models.IntegerField(
        null=True, blank=True, db_index=True, help_text="EMITTED->HANDLED latency in milliseconds"
    )
    congestion_flag = models.BooleanField(
        default=False, db_index=True, help_text="Set if latency > 5000ms"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["decision_id", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["congestion_flag", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.status}) [{self.event_id}]"
    
    @classmethod
    def store_outcome(cls, event_id, outcome) -> bool:
        """
        Store ABI outcome snapshot in audit log payload (best-effort).
        
        Uses safe read-modify-write pattern (backend-agnostic).
        Exception-safe - never raises, returns False on error.
        
        Args:
            event_id: UUID or string of event to update
            outcome: KernelOutcome instance
        
        Returns:
            True on success, False on failure
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Import here to avoid circular dependency
            from kernel.abi import KernelOutcome
            
            # SELECT payload (only fields needed)
            entry = cls.objects.filter(event_id=event_id).only('id', 'payload').first()
            
            if not entry:
                logger.warning(
                    "store_outcome: event not found",
                    extra={"event_id": str(event_id)},
                )
                return False
            
            # Mutate payload in Python (safe, backend-agnostic)
            payload = entry.payload.copy() if entry.payload else {}
            payload['abi'] = outcome.to_dict()
            
            # UPDATE payload
            cls.objects.filter(id=entry.id).update(payload=payload)
            
            return True
            
        except Exception as e:
            logger.error(
                "store_outcome: unexpected error (swallowed)",
                extra={
                    "event_id": str(event_id),
                    "error": str(e),
                },
                exc_info=True,
            )
            return False
    
    @classmethod
    def get_outcome(cls, event_id):
        """
        Retrieve ABI outcome from audit log (best-effort).
        
        Returns None if not found or invalid.
        
        Args:
            event_id: UUID or string of event
        
        Returns:
            KernelOutcome instance or None
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from kernel.abi import KernelOutcome
            
            entry = cls.objects.filter(event_id=event_id).only('payload').first()
            
            if entry and entry.payload and 'abi' in entry.payload:
                return KernelOutcome.from_dict(entry.payload['abi'])
            
            return None
            
        except Exception as e:
            logger.warning(
                "get_outcome: retrieval failed",
                extra={"event_id": str(event_id), "error": str(e)},
            )
            return None
    
    @classmethod
    def is_valid_transition(cls, current_status: str, new_status: str) -> bool:
        """
        Check if a state transition is valid (monotonic, no backtracking).
        
        Terminal states (HANDLED, REJECTED) cannot transition to any other state.
        
        Args:
            current_status: Current event status
            new_status: Proposed new status
        
        Returns:
            True if transition is allowed, False otherwise
        """
        # Terminal states cannot transition
        if current_status in cls.TERMINAL_STATES:
            return current_status == new_status  # Allow idempotent updates
        
        # All other transitions are valid
        return True
    
    @classmethod
    def safe_mark_handled(cls, event_id, handled_at=None, status=None, failure_reason=""):
        """
        Exception-safe telemetry recording for event handling outcomes.
        
        Best-effort update of handled_at, latency_ms, and congestion_flag.
        Never raises exceptions - swallows errors after logging.
        Enforces unidirectional state machine (no backtracking from terminal states).
        
        Args:
            event_id: UUID or string of event to mark
            handled_at: Timestamp when handled (defaults to now if None)
            status: New status (HANDLED/FAILED/REJECTED), defaults to HANDLED
            failure_reason: Optional failure reason string
        
        Returns:
            True if update succeeded, False if failed or invalid transition
        """
        import logging
        from django.utils import timezone
        
        logger = logging.getLogger(__name__)
        
        # Set defaults
        if handled_at is None:
            handled_at = timezone.now()
        if status is None:
            status = cls.STATUS_HANDLED
        
        try:
            # Fetch event with minimal columns + current status for transition check
            event = cls.objects.filter(event_id=event_id).only('event_id', 'created_at', 'status').first()
            
            if not event:
                logger.warning(
                    "safe_mark_handled: event not found",
                    extra={"event_id": str(event_id)},
                )
                return False
            
            # Check transition validity (monotonic state machine)
            if not cls.is_valid_transition(event.status, status):
                logger.warning(
                    "safe_mark_handled: invalid state transition blocked",
                    extra={
                        "event_id": str(event_id),
                        "current_status": event.status,
                        "requested_status": status,
                    },
                )
                return False
            
            # Compute telemetry (exception-safe)
            latency_ms = None
            congestion_flag = False
            
            try:
                if event.created_at:
                    delta = handled_at - event.created_at
                    latency_ms = int(delta.total_seconds() * 1000)
                    congestion_flag = latency_ms > 5000
            except Exception as e:
                # Latency computation failed - log but continue
                logger.warning(
                    "safe_mark_handled: latency computation failed",
                    extra={"event_id": str(event_id), "error": str(e)},
                )
            
            # Update event
            update_fields = {
                'status': status,
                'handled_at': handled_at,
                'latency_ms': latency_ms,
                'congestion_flag': congestion_flag,
            }
            
            if failure_reason:
                update_fields['failure_reason'] = failure_reason
            
            cls.objects.filter(event_id=event_id).update(**update_fields)
            
            if congestion_flag:
                logger.warning(
                    "Kernel congestion detected",
                    extra={
                        "event_id": str(event_id),
                        "latency_ms": latency_ms,
                    },
                )
            
            return True
            
        except Exception as e:
            logger.error(
                "safe_mark_handled: unexpected error",
                extra={
                    "event_id": str(event_id),
                    "error": str(e),
                },
                exc_info=True,
            )
            return False


class KernelIdempotencyRecord(models.Model):
    """
    Hot-path idempotency store for kernel event processing.
    
    Decouples hot-path "have we processed this key?" lookups from KernelAuditLog.
    Optimized for fast unique key checks and status queries.
    """

    STATUS_PROCESSED = "PROCESSED"
    STATUS_REJECTED = "REJECTED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = (
        (STATUS_PROCESSED, "Processed"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_FAILED, "Failed"),
    )
    
    # Terminal states - no transitions allowed FROM these states
    TERMINAL_STATES = {STATUS_PROCESSED, STATUS_REJECTED}

    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    event_type = models.CharField(max_length=128, db_index=True)
    decision_id = models.CharField(max_length=128, db_index=True)
    context_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PROCESSED, db_index=True
    )
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_event_id = models.UUIDField(null=True, blank=True, help_text="Pointer to KernelAuditLog")
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-processed_at"]
        indexes = [
            models.Index(fields=["event_type", "processed_at"]),
            models.Index(fields=["decision_id", "processed_at"]),
            models.Index(fields=["status", "processed_at"]),
        ]

    def __str__(self) -> str:
        return f"Idempotency({self.idempotency_key[:16]}...) [{self.status}]"
    
    @classmethod
    def is_valid_transition(cls, current_status: str, new_status: str) -> bool:
        """
        Check if a state transition is valid (monotonic, no backtracking).
        
        Terminal states (PROCESSED, REJECTED) cannot transition to FAILED.
        
        Args:
            current_status: Current record status
            new_status: Proposed new status
        
        Returns:
            True if transition is allowed, False otherwise
        """
        # Terminal states cannot transition to FAILED
        if current_status in cls.TERMINAL_STATES and new_status == cls.STATUS_FAILED:
            return False
        
        # Allow idempotent updates (same status)
        if current_status == new_status:
            return True
        
        # All other transitions are valid
        return True

