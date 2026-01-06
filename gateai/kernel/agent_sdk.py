import json
import hashlib
from typing import Dict, Any, List
from .laws import KernelOutcome, AgentAction, OUTCOME_TO_ALLOWED_ACTIONS

class KernelSDKError(Exception):
    """Base error for Kernel SDK."""
    pass

class KernelLawViolationError(KernelSDKError):
    """Raised when an agent attempts an illegal action according to Kernel Laws."""
    pass

class KernelABIError(KernelSDKError):
    """Raised when the Kernel reports an outcome unknown to the SDK (ABI drift)."""
    pass


def enforce_kernel_laws(outcome_code: str, intended_action: str) -> None:
    """
    Agent-side enforcement of the Kernel Constitution.
    
    This function MUST be called by the orchestrator before executing any 
    action based on a Kernel outcome.
    
    Args:
        outcome_code: The outcome_code returned by the Kernel.
        intended_action: The action the agent intends to take (from AgentAction).
    
    Raises:
        KernelLawViolationError: If the action is prohibited.
        KernelABIError: If the outcome code is unknown and doesn't follow failure patterns.
    """
    # 1. Check for explicit mapping
    allowed_actions = OUTCOME_TO_ALLOWED_ACTIONS.get(outcome_code)
    
    # 2. Forward Compatibility: Handle unknown FAILED_* codes
    if allowed_actions is None:
        if isinstance(outcome_code, str) and outcome_code.startswith("FAILED_"):
            # Default safety for future failure codes
            allowed_actions = [AgentAction.ABORT_ALERT]
        else:
            # Fatal ABI drift: The kernel is speaking a language we don't understand
            raise KernelABIError(f"Unknown Kernel outcome: {outcome_code}. ABI drift detected.")

    # 3. Enforcement
    if intended_action not in allowed_actions:
        raise KernelLawViolationError(
            f"Action {intended_action} is prohibited for outcome {outcome_code}. "
            f"Allowed: {allowed_actions}"
        )


def generate_context_hash(context_material: Dict[str, Any]) -> str:
    """
    Generate a deterministic SHA-256 hash representing a decision identity.
    
    Rules:
    - JSON keys MUST be sorted.
    - Compact separators (no whitespace).
    - SHA-256 for integrity.
    
    Args:
        context_material: Dict containing agent_id, task_id, plan_step, 
                         intent_code, and retry_epoch.
    
    Returns:
        Hexadecimal SHA-256 string.
    """
    # Force sorted keys and compact separators for stability
    stable_json = json.dumps(
        context_material,
        sort_keys=True,
        separators=(",", ":")
    )
    
    return hashlib.sha256(stable_json.encode('utf-8')).hexdigest()
