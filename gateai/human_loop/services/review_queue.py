"""
Human review queue service.

Manages creation and assignment of human review tasks for critical ATS signals.
Integrates with signal_delivery for notifications.
"""

import logging
from typing import Optional
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta

from human_loop.models import HumanReviewTask, MentorProfile
from ats_signals.models import ATSSignal

logger = logging.getLogger(__name__)


def create_review_task_for_signal(signal_id: str) -> Optional[HumanReviewTask]:
    """
    Create a human review task for a critical ATS signal.
    
    Args:
        signal_id: ID of the ATSSignal that requires review
        
    Returns:
        HumanReviewTask instance if created, None otherwise
        
    Raises:
        ATSSignal.DoesNotExist: If signal doesn't exist
        Exception: If task creation fails
    """
    try:
        signal = ATSSignal.objects.get(id=signal_id)
        
        # Only create review tasks for critical signals
        if signal.severity != 'critical':
            logger.debug(
                f"Skipping review task creation for non-critical signal {signal_id}",
                extra={'signal_id': signal_id, 'severity': signal.severity}
            )
            return None
        
        # Check if review task already exists for this signal
        existing_task = HumanReviewTask.objects.filter(signal=signal).first()
        if existing_task:
            logger.info(
                f"Review task already exists for signal {signal_id}: {existing_task.id}",
                extra={'signal_id': signal_id, 'task_id': existing_task.id}
            )
            return existing_task
        
        # Determine priority based on signal severity and type
        priority = 'urgent' if signal.severity == 'critical' else 'high'
        
        # Set due date (24 hours for critical signals)
        due_at = timezone.now() + timedelta(hours=24)
        
        # Extract context data from signal details
        # Include user_id from signal details for permission checks
        user_id = signal.details.get('user_id')
        context_data = {
            'signal_id': str(signal.id),
            'signal_type': signal.signal_type,
            'severity': signal.severity,
            'category': signal.category,
            'message': signal.message,
            'decision_slot_id': signal.decision_slot_id,
            **signal.details,  # Include any additional details from signal (including user_id)
        }
        # Ensure user_id is set for permission checks
        if user_id:
            context_data['user_id'] = str(user_id)
        
        # Create review task
        with transaction.atomic():
            review_task = HumanReviewTask.objects.create(
                signal=signal,
                decision_slot_id=signal.decision_slot_id,  # Rule 15: SIGNAL INTEGRITY
                task_type='signal_review',
                status='pending',
                priority=priority,
                context_data=context_data,
                due_at=due_at,
            )
            
            logger.info(
                f"Created review task {review_task.id} for critical signal {signal_id}",
                extra={
                    'task_id': review_task.id,
                    'signal_id': signal_id,
                    'decision_slot_id': signal.decision_slot_id,
                    'priority': priority,
                }
            )
            
            return review_task
            
    except ATSSignal.DoesNotExist:
        logger.error(f"Signal {signal_id} not found when creating review task")
        raise
    except Exception as e:
        logger.error(
            f"Failed to create review task for signal {signal_id}: {str(e)}",
            exc_info=True,
            extra={'signal_id': signal_id}
        )
        raise


def assign_review_task_to_mentor(task_id: int, mentor_profile: MentorProfile) -> bool:
    """
    Assign a review task to a mentor and notify them.
    
    Args:
        task_id: ID of the review task
        mentor_profile: MentorProfile to assign the task to
        
    Returns:
        True if assignment successful, False otherwise
    """
    try:
        task = HumanReviewTask.objects.get(id=task_id)
        
        if task.status == 'completed':
            logger.warning(f"Cannot assign completed task {task_id}")
            return False
        
        task.assign_to(mentor_profile.user)
        
        # Notify mentor about assigned task
        try:
            from signal_delivery.services.dispatcher import notify
            from signal_delivery.services.rules import NotificationType
            
            notify(
                NotificationType.MENTOR_REVIEW_TASK_ASSIGNED,
                context={
                    'mentor': mentor_profile.user,
                    'review_task_id': str(task.id),
                    'signal_id': str(task.signal.id),
                    'decision_slot_id': task.decision_slot_id,
                },
                title="Review Task Assigned",
                message=(
                    f"A review task has been assigned to you: {task.signal.message}. "
                    f"Signal type: {task.signal.signal_type}, Category: {task.signal.category}."
                ),
                priority='high' if task.priority == 'urgent' else 'normal',
                payload={
                    'review_task_id': str(task.id),
                    'signal_id': str(task.signal.id),
                    'signal_type': task.signal.signal_type,
                    'category': task.signal.category,
                    'decision_slot_id': task.decision_slot_id,
                },
            )
        except Exception as notify_error:
            # Log but don't fail assignment if notification fails
            logger.warning(
                f"Failed to notify mentor about assigned task {task_id}: {str(notify_error)}",
                exc_info=True
            )
        
        logger.info(
            f"Assigned review task {task_id} to mentor {mentor_profile.user.username}",
            extra={
                'task_id': task_id,
                'mentor_id': mentor_profile.id,
                'signal_id': task.signal.id,
            }
        )
        
        return True
        
    except HumanReviewTask.DoesNotExist:
        logger.error(f"Review task {task_id} not found")
        return False
    except Exception as e:
        logger.error(
            f"Failed to assign review task {task_id}: {str(e)}",
            exc_info=True
        )
        return False


def get_pending_review_tasks(assigned_to=None, priority=None):
    """
    Get pending review tasks.
    
    Args:
        assigned_to: Optional user to filter by
        priority: Optional priority level to filter by
        
    Returns:
        QuerySet of pending review tasks
    """
    queryset = HumanReviewTask.objects.filter(status='pending')
    
    if assigned_to:
        queryset = queryset.filter(assigned_to=assigned_to)
    
    if priority:
        queryset = queryset.filter(priority=priority)
    
    return queryset.order_by('-priority', '-created_at')


def get_critical_review_tasks():
    """
    Get all critical review tasks (urgent priority or overdue).
    
    Returns:
        QuerySet of critical review tasks
    """
    from django.utils import timezone
    
    return HumanReviewTask.objects.filter(
        models.Q(priority='urgent') | models.Q(due_at__lt=timezone.now(), status__in=['pending', 'assigned', 'in_progress'])
    ).order_by('-priority', '-created_at')

