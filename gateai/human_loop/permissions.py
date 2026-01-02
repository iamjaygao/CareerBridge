"""
Object-level permissions for Human Review Tasks.

Enforces that users can only access review tasks belonging to decision slots they own.
Staff/admin can access all tasks.

TODO: DecisionSlot model doesn't exist in decision_slots app.
Currently, decision_slot_id is just a string identifier with no ownership model.
When DecisionSlot model is created, update this module to use DecisionSlot.user field.
"""

from typing import Set
from django.contrib.auth import get_user_model

User = get_user_model()


def get_allowed_decision_slot_ids(user) -> Set[str]:
    """
    Get set of decision_slot_ids that the user is allowed to access.
    
    Args:
        user: Django user instance
        
    Returns:
        Set of decision_slot_id strings that user can access, or None for staff/superuser
        
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
    # For now, we use context_data to infer ownership.
    from human_loop.models import HumanReviewTask
    
    # Get decision_slot_ids from review tasks where context_data contains user_id
    review_tasks = HumanReviewTask.objects.filter(
        context_data__user_id=str(user.id)
    ).values_list('decision_slot_id', flat=True).distinct()
    
    return set(review_tasks)


def filter_review_tasks_by_ownership(queryset, user):
    """
    Filter HumanReviewTask queryset to only include tasks user is allowed to access.
    
    Args:
        queryset: HumanReviewTask queryset
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

