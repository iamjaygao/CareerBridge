"""
Kernel callback implementations for decision_slots app.

Provides resource release logic to kernel via callback registration.
MUST NOT import kernel_events to maintain Isolation Wall.
"""

import logging
from typing import Any, Dict

from decision_slots.models import ResourceLock

logger = logging.getLogger(__name__)


def release_locks_for_failure(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Release locks associated with a failed kernel event.
    
    Called by kernel failure handler via callback mechanism.
    Examines payload and releases appropriate locks.
    
    Strategy:
    - If payload has decision_id: release all locks for that decision (full rollback)
    - Otherwise, if payload has resource_id: try to release specific lock (best-effort)
    
    Args:
        payload: Event payload dict (from kernel event)
    
    Returns:
        dict with keys:
        - success: bool
        - released_count: int (number of locks released)
        - error: str (if success=False)
    """
    try:
        decision_id = payload.get("decision_id")
        resource_id = payload.get("resource_id")
        reason = payload.get("reason", "Kernel failure")
        
        if not decision_id and not resource_id:
            return {
                "success": False,
                "released_count": 0,
                "error": "No decision_id or resource_id in payload",
            }
        
        # Strategy 1: Full rollback if we have decision_id
        if decision_id:
            count = ResourceLock.release_for_decision(
                decision_id=str(decision_id),
                reason=reason,
            )
            
            return {
                "success": True,
                "released_count": count,
            }
        
        # Strategy 2: Best-effort single lock release by resource_id
        # (legacy compatibility path)
        if resource_id:
            resource_type = payload.get("resource_type", ResourceLock.RESOURCE_TYPE_APPOINTMENT)
            
            # Try to find and release lock by resource_id (may not have decision_id)
            from django.db import transaction
            
            with transaction.atomic():
                lock = (
                    ResourceLock.objects.select_for_update()
                    .filter(resource_id=resource_id, resource_type=resource_type, status='active')
                    .first()
                )
                
                if lock:
                    success = lock.release_and_audit(reason=reason)
                    return {
                        "success": True,
                        "released_count": 1 if success else 0,
                    }
        
        # No locks found
        return {
            "success": True,
            "released_count": 0,
        }
    
    except Exception as e:
        logger.exception(
            "release_locks_for_failure: unexpected error",
            extra={"payload_keys": list(payload.keys())},
        )
        return {
            "success": False,
            "released_count": 0,
            "error": str(e),
        }

