"""
GateAI Kernel Laws (SDK)
Canonical constants for Outcome-to-Action mapping.
"""

class KernelOutcome:
    """Canonical Outcome Codes from the Kernel ABI."""
    OK = "OK"
    REPLAY = "REPLAY"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FATAL = "FAILED_FATAL"


class AgentAction:
    """Standardized action guidance for Agent orchestration."""
    PROCEED = "PROCEED"
    NOOP_SUCCESS = "NOOP_SUCCESS"
    WAIT_RETRY = "WAIT_RETRY"
    BACKOFF_RETRY = "BACKOFF_RETRY"
    ABORT_ALERT = "ABORT_ALERT"


# Canonical Outcome → Action Policy
# Higher-level orchestration logic should follow these mappings
# to ensure compliance with the Kernel Constitution.
OUTCOME_TO_ALLOWED_ACTIONS = {
    KernelOutcome.OK: [AgentAction.PROCEED],
    KernelOutcome.REPLAY: [AgentAction.NOOP_SUCCESS, AgentAction.PROCEED],
    KernelOutcome.CONFLICT: [AgentAction.WAIT_RETRY],
    KernelOutcome.FAILED_RETRYABLE: [AgentAction.BACKOFF_RETRY],
    KernelOutcome.REJECTED: [AgentAction.ABORT_ALERT],
    KernelOutcome.FAILED_FATAL: [AgentAction.ABORT_ALERT],
}
