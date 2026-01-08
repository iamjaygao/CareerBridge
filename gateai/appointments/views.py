from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime, timedelta

from appointments.models import TimeSlot, Appointment, AppointmentRequest
from appointments.serializers import (
    TimeSlotSerializer, AppointmentSerializer, AppointmentRequestSerializer,
    AppointmentUpdateSerializer, TimeSlotCreateSerializer
)
from signal_delivery.models import Notification
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from django.contrib.auth import get_user_model

# Kernel event system (Day 1 isolation)
from gateai.kernel_events import emit_kernel_event


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _sync_slot_bookings(slot):
    """Update slot booking count based on confirmed/completed appointments"""
    if not slot:
        return
    booked_count = Appointment.objects.filter(
        time_slot=slot,
        status__in=['confirmed', 'completed']
    ).count()
    if slot.current_bookings != booked_count:
        slot.current_bookings = booked_count
        slot.save(update_fields=['current_bookings'])


def _format_request_details(appointment_request) -> str:
    """Format appointment request details for notifications"""
    title = appointment_request.title or "Appointment request"
    if appointment_request.preferred_date and appointment_request.preferred_time_start:
        time_label = appointment_request.preferred_time_start.strftime('%H:%M')
        date_label = appointment_request.preferred_date.strftime('%Y-%m-%d')
        return f"{title} on {date_label} {time_label}"
    if appointment_request.preferred_date:
        date_label = appointment_request.preferred_date.strftime('%Y-%m-%d')
        return f"{title} on {date_label}"
    return title


def _notify_staff_appointment_cancelled(appointment) -> None:
    """Send notification to staff when appointment is cancelled"""
    User = get_user_model()
    staff_users = User.objects.filter(role="staff")
    if not staff_users.exists():
        return

    mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
    student_name = appointment.user.get_full_name() or appointment.user.username
    appointment_details = appointment.get_notification_details()
    message = (
        f'Appointment ({appointment_details}) between {student_name} and {mentor_name} '
        f'was cancelled and may need follow-up.'
    )

    for staff_user in staff_users:
        notify(
            NotificationType.STAFF_APPOINTMENT_CANCELLED,
            context={
                'appointment_id': appointment.id,
                'staff': staff_user,
            },
            title='Appointment cancelled - staff follow-up',
            message=message,
            priority='high',
            related_appointment=appointment,
            payload=appointment.get_notification_payload(),
        )


def _notify_staff_user_feedback(appointment) -> None:
    """Send notification to staff when user submits feedback"""
    User = get_user_model()
    staff_users = User.objects.filter(role="staff")
    if not staff_users.exists():
        return

    mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
    student_name = appointment.user.get_full_name() or appointment.user.username
    appointment_details = appointment.get_notification_details()
    message = (
        f'New user feedback for {appointment_details} with {mentor_name}. '
        f'From {student_name}.'
    )

    for staff_user in staff_users:
        notify(
            NotificationType.STAFF_USER_FEEDBACK_SUBMITTED,
            context={
                'feedback_id': appointment.id,
                'appointment_id': appointment.id,
                'staff': staff_user,
            },
            title='User feedback submitted',
            message=message,
            priority='normal',
            related_appointment=appointment,
            payload=appointment.get_notification_payload(),
        )


# ============================================================================
# APPOINTMENT VIEWS (DOMAIN CRUD)
# ============================================================================

class AppointmentListView(generics.ListCreateAPIView):
    """Appointment list and creation"""
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.filter(user=user)

        now = timezone.now()

        upcoming = self.request.query_params.get('upcoming')

        if upcoming == 'true':
            queryset = queryset.filter(
                scheduled_start__gt=now,
                status__in=['pending', 'confirmed']
            )

        elif upcoming == 'false':
            queryset = queryset.filter(
                Q(status__in=['completed', 'cancelled', 'expired']) |
                Q(
                    status='confirmed',
                    scheduled_end__lt=now
                )
            )

        return queryset.order_by('-scheduled_start')
    
    def perform_create(self, serializer):
        serializer.save()


class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Appointment details, update and delete"""
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(user=user)


class AppointmentCancelView(APIView):
    """Cancel appointment"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, user=request.user)

        if not appointment.can_cancel:
            return Response(
                {"error": "Cannot cancel this appointment"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '')
        appointment.cancel_appointment(reason=reason, cancelled_by='user')
        _sync_slot_bookings(appointment.time_slot)

        mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
        appointment_details = appointment.get_notification_details()
        notify(
            NotificationType.APPOINTMENT_CANCELLED,
            context={
                'appointment_id': appointment.id,
                'student': appointment.user,
                'mentor': appointment.mentor.user,
            },
            title='Appointment cancelled',
            message=(
                f'Appointment ({appointment_details}) between {appointment.user.get_full_name() or appointment.user.username} '
                f'and {mentor_name} has been cancelled.'
            ),
            priority='high',
            related_appointment=appointment,
            payload=appointment.get_notification_payload(),
        )
        _notify_staff_appointment_cancelled(appointment)

        return Response({"message": "Appointment cancelled successfully"})


class AppointmentRateView(APIView):
    """User rates appointment"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, user=request.user)

        if appointment.status != 'completed':
            return Response(
                {"error": "Can only rate completed appointments"},
                status=status.HTTP_400_BAD_REQUEST
            )

        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')

        if not rating or not (1 <= int(rating) <= 5):
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.user_rating = rating
        appointment.user_feedback = feedback
        appointment.save()

        from human_loop.models import MentorReview
        from django.db.models import Avg, Count
        MentorReview.objects.update_or_create(
            mentor=appointment.mentor,
            user=appointment.user,
            defaults={
                'rating': rating,
                'comment': feedback,
            },
        )
        summary = MentorReview.objects.filter(mentor=appointment.mentor).aggregate(
            average=Avg('rating'),
            total=Count('id')
        )
        appointment.mentor.average_rating = summary['average'] or 0
        appointment.mentor.total_reviews = summary['total'] or 0
        appointment.mentor.save(update_fields=['average_rating', 'total_reviews'])

        appointment_details = appointment.get_notification_details()
        mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
        notify(
            NotificationType.MENTOR_SUBMITTED_FEEDBACK,
            context={
                'appointment_id': appointment.id,
                'student': appointment.user,
            },
            title='Feedback submitted',
            message=f'Thank you for rating your {appointment_details} with {mentor_name}.',
            priority='low',
            related_appointment=appointment,
            payload=appointment.get_notification_payload(),
        )
        _notify_staff_user_feedback(appointment)

        if appointment.mentor.average_rating < 3 and appointment.mentor.total_reviews >= 3:
            User = get_user_model()
            admin_users = User.objects.filter(role="admin")
            for admin_user in admin_users:
                notify(
                    NotificationType.ADMIN_MENTOR_LOW_RATING,
                    context={
                        'mentor_id': appointment.mentor.id,
                        'admin': admin_user,
                    },
                    title='Mentor rating dropped',
                    message=(
                        f'Mentor {mentor_name} rating is now {appointment.mentor.average_rating:.1f} '
                        f'({appointment.mentor.total_reviews} reviews).'
                    ),
                    priority='high',
                    related_mentor=appointment.mentor,
                    payload={'mentor_id': appointment.mentor.id},
                )

        return Response({"message": "Rating submitted successfully"})


class MentorAppointmentListView(generics.ListAPIView):
    """Mentor views their appointments"""
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Ensure user is a mentor
        if not hasattr(self.request.user, 'mentor_profile'):
            return Appointment.objects.none()
        
        return Appointment.objects.filter(mentor=self.request.user.mentor_profile)


class MentorAppointmentStatusView(APIView):
    """Mentor updates appointment status"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if not hasattr(request.user, 'mentor_profile'):
            return Response(
                {"error": "Only mentors can update appointments"},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
            mentor=request.user.mentor_profile
        )
        old_status = appointment.status
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            appointment.refresh_from_db()
            _sync_slot_bookings(appointment.time_slot)

            if appointment.status in ['confirmed', 'cancelled', 'completed'] and appointment.status != old_status:
                mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
                student_name = appointment.user.get_full_name() or appointment.user.username
                appointment_details = appointment.get_notification_details()
                priority = 'high' if appointment.status == 'cancelled' else 'normal'
                status_text = appointment.get_status_display()

                event_type = (
                    NotificationType.APPOINTMENT_CANCELLED
                    if appointment.status == 'cancelled'
                    else NotificationType.APPOINTMENT_CONFIRMED
                )
                notify(
                    event_type,
                    context={
                        'appointment_id': appointment.id,
                        'student': appointment.user,
                        'mentor': appointment.mentor.user,
                    },
                    title='Appointment status updated',
                    message=(
                        f'Appointment ({appointment_details}) between {student_name} and {mentor_name} '
                        f'is now {status_text}.'
                    ),
                    priority=priority,
                    related_appointment=appointment,
                    payload=appointment.get_notification_payload(),
                )
                if appointment.status == 'cancelled':
                    _notify_staff_appointment_cancelled(appointment)

            if appointment.status == 'completed' and old_status != 'completed':
                mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
                appointment_details = appointment.get_notification_details()
                if not Notification.objects.filter(
                    user=appointment.user,
                    notification_type='system_announcement',
                    related_appointment=appointment,
                    title='Please review your session'
                ).exists():
                    notify(
                        NotificationType.APPOINTMENT_REVIEW_REMINDER,
                        context={
                            'appointment_id': appointment.id,
                            'student': appointment.user,
                        },
                        title='Please review your session',
                        message=f'Please share your feedback about your {appointment_details} with {mentor_name}.',
                        priority='normal',
                        related_appointment=appointment,
                        payload={
                            **appointment.get_notification_payload(),
                            'action': 'review_appointment',
                        },
                    )
                # Day 1: Kernel event replaces direct payment execution
                lock_boundary = appointment.time_slot.reserved_until or appointment.scheduled_end
                emit_kernel_event(
                    "APPOINTMENT_COMPLETED",
                    {
                        "appointment_id": appointment.id,
                        "decision_id": f"appointment:{appointment.id}",
                        "resource_id": appointment.id,
                        "owner_id": appointment.user_id,
                        "action_type": "APPOINTMENT_COMPLETED",
                        "lock_expires_at": lock_boundary.astimezone(timezone.utc).isoformat() if lock_boundary else None,
                    }
                )

            return Response(AppointmentSerializer(appointment).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentRequestListView(generics.ListCreateAPIView):
    """Appointment request list and creation"""
    serializer_class = AppointmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # If mentor, view received requests
        if hasattr(user, 'mentor_profile'):
            return AppointmentRequest.objects.filter(mentor=user.mentor_profile)
        
        # If regular user, view requests they sent
        return AppointmentRequest.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save()


class AppointmentRequestDetailView(generics.RetrieveUpdateAPIView):
    """Appointment request details and update"""
    serializer_class = AppointmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'mentor_profile'):
            return AppointmentRequest.objects.filter(mentor=user.mentor_profile)
        return AppointmentRequest.objects.filter(user=user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def appointment_request_respond(request, pk):
    """Mentor responds to appointment request"""
    if not hasattr(request.user, 'mentor_profile'):
        return Response(
            {"error": "Only mentors can respond to requests"},
            status=status.HTTP_403_FORBIDDEN
        )

    appointment_request = get_object_or_404(
        AppointmentRequest,
        pk=pk,
        mentor=request.user.mentor_profile
    )

    response_text = request.data.get('response', '')
    status_action = request.data.get('status')
    suggested_slots = request.data.get('suggested_time_slots', [])

    if status_action not in ['accepted', 'rejected']:
        return Response(
            {"error": "Status must be 'accepted' or 'rejected'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    appointment_request.status = status_action
    appointment_request.mentor_response = response_text
    appointment_request.suggested_time_slots = suggested_slots
    appointment_request.save()

    mentor_name = appointment_request.mentor.user.get_full_name() or appointment_request.mentor.user.username
    request_details = _format_request_details(appointment_request)
    request_payload = {
        'appointment_details': request_details,
        'request_id': appointment_request.id,
        'mentor_id': appointment_request.mentor_id,
        'mentor_name': mentor_name,
        'student_id': appointment_request.user_id,
        'student_name': appointment_request.user.get_full_name() or appointment_request.user.username,
    }
    if status_action == 'accepted':
        notify(
            NotificationType.APPOINTMENT_CONFIRMED,
            context={
                'appointment_id': appointment_request.id,
                'student': appointment_request.user,
                'mentor': appointment_request.mentor.user,
            },
            title='Appointment confirmed',
            message=(
                f'Appointment request ({request_details}) between {appointment_request.user.get_full_name() or appointment_request.user.username} '
                f'and {mentor_name} was accepted.'
            ),
            priority='normal',
            related_mentor=appointment_request.mentor,
            payload=request_payload,
        )
    else:
        notify(
            NotificationType.APPOINTMENT_REJECTED,
            context={
                'appointment_id': appointment_request.id,
                'student': appointment_request.user,
            },
            title='Appointment rejected',
            message=f'{mentor_name} rejected your appointment request ({request_details}).',
            priority='normal',
            related_mentor=appointment_request.mentor,
            payload=request_payload,
        )

    return Response({"message": "Response submitted successfully"})


class AppointmentStatsView(generics.GenericAPIView):
    """Appointment statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # User appointment statistics
        if not hasattr(user, 'mentor_profile'):
            total_appointments = Appointment.objects.filter(user=user).count()
            upcoming_appointments = Appointment.objects.filter(
                user=user,
                scheduled_start__gt=timezone.now(),
                status__in=['pending', 'confirmed']
            ).count()
            completed_appointments = Appointment.objects.filter(
                user=user,
                status='completed'
            ).count()
            
            return Response({
                'total_appointments': total_appointments,
                'upcoming_appointments': upcoming_appointments,
                'completed_appointments': completed_appointments,
            })
        
        # Mentor appointment statistics
        else:
            total_appointments = Appointment.objects.filter(mentor=user.mentor_profile).count()
            pending_appointments = Appointment.objects.filter(
                mentor=user.mentor_profile,
                status='pending'
            ).count()
            today_appointments = Appointment.objects.filter(
                mentor=user.mentor_profile,
                scheduled_start__date=timezone.now().date()
            ).count()
            
            return Response({
                'total_appointments': total_appointments,
                'pending_appointments': pending_appointments,
                'today_appointments': today_appointments,
            })

