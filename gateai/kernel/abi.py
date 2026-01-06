"""
GateAI Kernel ABI (Application Binary Interface) v3.0

Defines stable, immutable contracts for kernel execution outcomes and error codes.
This module is the single source of truth for kernel-level semantics.

ABI Stability Guarantees:
- Outcome codes may be ADDED, never removed or renamed
- Error codes may be ADDED, never removed or renamed
- KernelOutcome fields are part of the ABI contract
- Schema version "3.0" indicates this ABI generation

Domain Agnostic:
- NO imports from appointments, payments, human_loop, decision_slots
- Error codes use generic, kernel-level terminology only
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ABI Version (semantic versioning)
ABI_VERSION = "3.0"


class KernelOutcomeCode:
    """
    Immutable kernel execution outcome codes (ABI v3.0).
    
    Closed set of possible execution results. May be extended in future
    versions but existing codes must never be renamed or removed.
    """
    OK = "OK"                          # Successfully processed
    REPLAY = "REPLAY"                  # Idempotent replay detected (no-op)
    REJECTED = "REJECTED"              # Policy/contract violation
    CONFLICT = "CONFLICT"              # Resource contention (retry recommended)
    FAILED_RETRYABLE = "FAILED_RETRYABLE"  # Transient failure (retry recommended)
    FAILED_FATAL = "FAILED_FATAL"      # Permanent failure (do not retry)


class KernelErrorCode:
    """
    Immutable kernel error codes (ABI v3.0).
    
    Namespaced with KERNEL/* prefix for kernel-level errors.
    Add-only policy: new codes may be added, existing codes never removed.
    
    Domain-agnostic: uses generic terminology, not business logic terms.
    """
    # Idempotency errors
    KERNEL_IDEMPOTENCY_REPLAY = "KERNEL/IDEMPOTENCY_REPLAY"
    KERNEL_IDEMPOTENCY_VIOLATION = "KERNEL/IDEMPOTENCY_VIOLATION"
    
    # Context validation errors
    KERNEL_CONTEXT_HASH_MISMATCH = "KERNEL/CONTEXT_HASH_MISMATCH"
    KERNEL_INVALID_PAYLOAD = "KERNEL/INVALID_PAYLOAD"
    
    # Execution errors (domain-agnostic)
    KERNEL_LISTENER_EXCEPTION = "KERNEL/LISTENER_EXCEPTION"
    KERNEL_CALLBACK_EXCEPTION = "KERNEL/CALLBACK_EXCEPTION"
    KERNEL_EXTERNAL_DEPENDENCY_FAILURE = "KERNEL/EXTERNAL_DEPENDENCY_FAILURE"
    
    # Resource errors
    KERNEL_RESOURCE_LOCK_EXPIRED = "KERNEL/RESOURCE_LOCK_EXPIRED"
    KERNEL_RESOURCE_CONFLICT = "KERNEL/RESOURCE_CONFLICT"
    
    # Generic fallback
    KERNEL_GENERIC_FAILURE = "KERNEL/GENERIC_FAILURE"


@dataclass
class KernelOutcome:
    """
    Standardized kernel execution outcome (ABI v3.0).
    
    Immutable contract - all fields are part of the public ABI.
    Serializes to/from dict for storage in KernelAuditLog.payload["abi"].
    
    Required fields (always present):
        abi_version: ABI version string ("3.0")
        outcome_code: One of KernelOutcomeCode.*
        retryable: True if client should retry operation
        terminal: True if state is final (no further processing)
        public_message: Safe for external display (user-facing)
    
    Optional fields (may be None):
        error_code: One of KernelErrorCode.*, if error occurred
        internal_reason: Debugging info, not for public display
        http_hint: Suggested HTTP status code (informational)
        extras: Extensibility dict for additional context
    """
    abi_version: str
    outcome_code: str
    retryable: bool
    terminal: bool
    public_message: str
    
    error_code: Optional[str] = None
    internal_reason: Optional[str] = None
    http_hint: Optional[int] = None
    extras: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """
        Serialize for storage in KernelAuditLog.payload["abi"].
        
        Returns:
            dict with all fields (None values preserved)
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "KernelOutcome":
        """
        Deserialize from audit log payload.
        
        Handles missing optional fields gracefully.
        
        Args:
            data: dict from KernelAuditLog.payload["abi"]
        
        Returns:
            KernelOutcome instance
        
        Raises:
            KeyError: if required fields missing
        """
        return cls(
            abi_version=data.get("abi_version", ABI_VERSION),
            outcome_code=data["outcome_code"],
            retryable=data["retryable"],
            terminal=data["terminal"],
            public_message=data["public_message"],
            error_code=data.get("error_code"),
            internal_reason=data.get("internal_reason"),
            http_hint=data.get("http_hint"),
            extras=data.get("extras", {}),
        )


def classify_failure(
    error_code: Optional[str] = None,
    exception: Optional[Exception] = None,
    context_hash_mismatch: bool = False,
    idempotency_replay: bool = False,
    resource_conflict: bool = False,
    callback_failure: bool = False,
    internal_reason: Optional[str] = None,
) -> KernelOutcome:
    """
    Deterministic failure classification (ABI v3.0).
    
    Maps error conditions to standardized outcomes with retry/terminal semantics.
    
    Precedence (first match wins):
    1. idempotency_replay -> REPLAY
    2. context_hash_mismatch -> REJECTED
    3. resource_conflict -> CONFLICT
    4. callback_failure -> FAILED_FATAL
    5. exception (generic) -> FAILED_RETRYABLE
    6. error_code specific mapping
    7. fallback -> FAILED_FATAL
    
    Args:
        error_code: Specific error code to classify
        exception: Python exception that occurred
        context_hash_mismatch: True if context validation failed
        idempotency_replay: True if operation was already processed
        resource_conflict: True if resource contention detected
        callback_failure: True if system callback failed
        internal_reason: Additional debug context
    
    Returns:
        KernelOutcome with deterministic retry/terminal guidance
    """
    # Priority 1: Idempotent replay
    if idempotency_replay:
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.REPLAY,
            retryable=False,
            terminal=True,
            public_message="Operation already processed (idempotent replay)",
            error_code=KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY,
            internal_reason=internal_reason,
            http_hint=200,  # Successful replay is OK
        )
    
    # Priority 2: Context validation failure
    if context_hash_mismatch:
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.REJECTED,
            retryable=False,
            terminal=True,
            public_message="Context validation failed",
            error_code=KernelErrorCode.KERNEL_CONTEXT_HASH_MISMATCH,
            internal_reason=internal_reason,
            http_hint=400,
        )
    
    # Priority 3: Resource conflict
    if resource_conflict:
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.CONFLICT,
            retryable=True,
            terminal=False,
            public_message="Resource conflict detected, retry recommended",
            error_code=KernelErrorCode.KERNEL_RESOURCE_CONFLICT,
            internal_reason=internal_reason,
            http_hint=409,
        )
    
    # Priority 4: Critical callback failure
    if callback_failure:
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.FAILED_FATAL,
            retryable=False,
            terminal=True,
            public_message="Critical system callback failure",
            error_code=KernelErrorCode.KERNEL_CALLBACK_EXCEPTION,
            internal_reason=internal_reason or (str(exception) if exception else None),
            http_hint=500,
        )
    
    # Priority 5: Generic exception (retryable)
    if exception:
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.FAILED_RETRYABLE,
            retryable=True,
            terminal=False,
            public_message="Transient failure, retry recommended",
            error_code=KernelErrorCode.KERNEL_LISTENER_EXCEPTION,
            internal_reason=internal_reason or str(exception),
            http_hint=503,
        )
    
    # Priority 6: Specific error code mapping
    if error_code:
        if error_code == KernelErrorCode.KERNEL_EXTERNAL_DEPENDENCY_FAILURE:
            return KernelOutcome(
                abi_version=ABI_VERSION,
                outcome_code=KernelOutcomeCode.FAILED_RETRYABLE,
                retryable=True,
                terminal=False,
                public_message="External service unavailable",
                error_code=error_code,
                internal_reason=internal_reason,
                http_hint=503,
            )
        
        if error_code == KernelErrorCode.KERNEL_RESOURCE_LOCK_EXPIRED:
            return KernelOutcome(
                abi_version=ABI_VERSION,
                outcome_code=KernelOutcomeCode.REJECTED,
                retryable=False,
                terminal=True,
                public_message="Resource lock expired",
                error_code=error_code,
                internal_reason=internal_reason,
                http_hint=410,
            )
        
        if error_code == KernelErrorCode.KERNEL_INVALID_PAYLOAD:
            return KernelOutcome(
                abi_version=ABI_VERSION,
                outcome_code=KernelOutcomeCode.REJECTED,
                retryable=False,
                terminal=True,
                public_message="Invalid request payload",
                error_code=error_code,
                internal_reason=internal_reason,
                http_hint=400,
            )
    
    # Priority 7: Fallback (unknown error)
    return KernelOutcome(
        abi_version=ABI_VERSION,
        outcome_code=KernelOutcomeCode.FAILED_FATAL,
        retryable=False,
        terminal=True,
        public_message="Unknown failure",
        error_code=error_code or KernelErrorCode.KERNEL_GENERIC_FAILURE,
        internal_reason=internal_reason,
        http_hint=500,
    )


def classify_success(
    claimed: bool = True,
    message: str = "Processed successfully",
    **extras
) -> KernelOutcome:
    """
    Classify successful execution (ABI v3.0).
    
    Maps success conditions to OK or REPLAY outcomes.
    
    Args:
        claimed: True if operation was performed, False if idempotent replay
        message: Public-facing success message
        **extras: Additional context for outcome.extras
    
    Returns:
        KernelOutcome with OK or REPLAY code
    """
    if not claimed:
        # Idempotent replay detected
        return KernelOutcome(
            abi_version=ABI_VERSION,
            outcome_code=KernelOutcomeCode.REPLAY,
            retryable=False,
            terminal=True,
            public_message="Operation already completed (idempotent)",
            error_code=KernelErrorCode.KERNEL_IDEMPOTENCY_REPLAY,
            http_hint=200,
            extras=extras,
        )
    
    return KernelOutcome(
        abi_version=ABI_VERSION,
        outcome_code=KernelOutcomeCode.OK,
        retryable=False,
        terminal=True,
        public_message=message,
        http_hint=200,
        extras=extras,
    )


# ABI v3.0 Outcome -> KernelAuditLog.status mapping
# (preserves Step 2 state machine rules)
OUTCOME_TO_STATUS_MAP = {
    KernelOutcomeCode.OK: "HANDLED",
    KernelOutcomeCode.REPLAY: "REJECTED",
    KernelOutcomeCode.REJECTED: "REJECTED",
    KernelOutcomeCode.CONFLICT: "FAILED",
    KernelOutcomeCode.FAILED_RETRYABLE: "FAILED",
    KernelOutcomeCode.FAILED_FATAL: "FAILED",
}


def map_outcome_to_status(outcome: KernelOutcome) -> str:
    """
    Map ABI outcome code to KernelAuditLog status.
    
    Preserves Step 2 state machine semantics.
    
    Args:
        outcome: KernelOutcome to map
    
    Returns:
        Status string (HANDLED/REJECTED/FAILED)
    """
    return OUTCOME_TO_STATUS_MAP.get(outcome.outcome_code, "FAILED")

