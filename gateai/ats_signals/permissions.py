"""
Object-level permissions for ATS Signals.

Enforces that users can only access signals belonging to decision slots they own.
Staff/admin can access all signals.

TODO: DecisionSlot model doesn't exist in decision_slots app.
Currently, decision_slot_id is just a string identifier with no ownership model.
When DecisionSlot model is created, update this module to:
1. Query DecisionSlot.objects.filter(user=request.user) to get owned slots
2. Use DecisionSlot.id values to filter signals
3. Remove the workaround logic below
"""

from typing import List, Set
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


def get_allowed_decision_slot_ids(user) -> Set[str]:
    """
    Get set of decision_slot_ids that the user is allowed to access.
    
    Args:
        user: Django user instance
        
    Returns:
        Set of decision_slot_id strings that user can access
        
    TODO: When DecisionSlot model exists, replace this with:
        if user.is_staff or user.is_superuser:
            return None  # All slots allowed
        slots = DecisionSlot.objects.filter(user=user)
        return set(slots.values_list('id', flat=True))
    """
    # Staff and superusers can access all
    if user.is_staff or user.is_superuser:
        return None  # None means "all allowed"
    
    # TODO: DecisionSlot model doesn't exist.
    # For now, we use a workaround: check HumanReviewTask.context_data
    # to infer ownership. This is not ideal but works until DecisionSlot model exists.
    from human_loop.models import HumanReviewTask
    
    # Get decision_slot_ids from review tasks where context_data contains user_id
    # This is a best-effort approach until DecisionSlot model exists
    review_tasks = HumanReviewTask.objects.filter(
        context_data__user_id=str(user.id)
    ).values_list('decision_slot_id', flat=True).distinct()
    
    allowed_ids = set(review_tasks)
    
    # Also check if user_id is in signal details (fallback)
    # Some signals might have user_id in details
    from ats_signals.models import ATSSignal
    
    signals_with_user = ATSSignal.objects.filter(
        details__user_id=str(user.id)
    ).values_list('decision_slot_id', flat=True).distinct()
    
    allowed_ids.update(signals_with_user)
    
    return allowed_ids


def filter_signals_by_ownership(queryset, user):
    """
    Filter ATSSignal queryset to only include signals user is allowed to access.
    
    Args:
        queryset: ATSSignal queryset
        user: Django user instance
        
    Returns:
        Filtered queryset
    """
    allowed_ids = get_allowed_decision_slot_ids(user)
    
    # Staff/superuser can see all
    if allowed_ids is None:
        return queryset
    
    # Regular users can only see their own
    if not allowed_ids:
        return queryset.none()  # No allowed slots -> empty queryset
    
    return queryset.filter(decision_slot_id__in=allowed_ids)


def user_can_access_decision_slot(user, decision_slot_id: str) -> bool:
    """
    Check if user can access a specific decision slot.
    
    Args:
        user: Django user instance
        decision_slot_id: Decision slot ID to check
        
    Returns:
        True if user can access, False otherwise
    """
    allowed_ids = get_allowed_decision_slot_ids(user)
    
    # Staff/superuser can access all
    if allowed_ids is None:
        return True
    
    # Regular users can only access their own
    return decision_slot_id in allowed_ids

