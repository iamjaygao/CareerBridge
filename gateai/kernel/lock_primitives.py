"""
Kernel-level lock release primitives.

Stateless helpers for computing lock release audit payloads.
NO ORM imports. NO domain logic. Pure computation only.
"""

from typing import Any, Dict, Optional
from django.utils import timezone


def compute_lock_release_audit(
    decision_id: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[Any] = None,
    resource_key: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute standardized audit payload for lock release events.
    
    Pure function - no side effects, no DB access.
    Returns a dict suitable for KernelAuditLog.payload.
    
    Args:
        decision_id: Decision ID grouping the lock(s)
        resource_type: Type of resource (if partial release)
        resource_id: ID of specific resource (if partial release)
        resource_key: Optional key for composite locks (if partial release)
        reason: Human-readable release reason
    
    Returns:
        dict with standardized audit fields
    """
    payload = {
        "decision_id": str(decision_id),
        "released_at": timezone.now().isoformat(),
        "release_type": "FULL" if (resource_type is None and resource_id is None) else "PARTIAL",
    }
    
    if resource_type is not None:
        payload["resource_type"] = str(resource_type)
    
    if resource_id is not None:
        payload["resource_id"] = str(resource_id)
    
    if resource_key is not None:
        payload["resource_key"] = str(resource_key)
    
    if reason:
        payload["reason"] = str(reason)
    
    return payload

