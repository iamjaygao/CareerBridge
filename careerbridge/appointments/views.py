from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime, timedelta

from .models import TimeSlot, Appointment, AppointmentRequest
from .serializers import (
    TimeSlotSerializer, AppointmentSerializer, AppointmentRequestSerializer,
    AppointmentUpdateSerializer, TimeSlotCreateSerializer
)
from notifications.models import Notification
from notifications.services.dispatcher import notify
from notifications.services.rules import NotificationType
from django.contrib.auth import get_user_model
from payments.services import schedule_payout_for_appointment

def _sync_slot_bookings(slot):
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

class TimeSlotListView(generics.ListAPIView):
    """Get available time slot list"""
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        FINAL TimeSlot provider.

        Contract:
        - Return ONLY real TimeSlot records
        - NO state mutation
        - NO availability inference
        """

        mentor_id = self.request.query_params.get('mentor_id')
        date = self.request.query_params.get('date')
        from_date_str = self.request.query_params.get('from')
        to_date_str = self.request.query_params.get('to')
        service_id = self.request.query_params.get('service_id')

        if not mentor_id:
            return TimeSlot.objects.none()

        now = timezone.now()

        # Base availability filter: allow only truly available slots or expired locks
        availability_filter = Q(is_available=True) | Q(is_available=False, reserved_until__isnull=False, reserved_until__lte=now)

        # Single-day query: mentor_id + date
        if date:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return TimeSlot.objects.none()

            qs = (
                TimeSlot.objects
                .filter(
                    mentor_id=mentor_id,
                    start_time__date=target_date,
                )
                .filter(availability_filter)
                .filter(
                    Q(reserved_until__isnull=True) | Q(reserved_until__lte=now)
                )
                .exclude(reserved_appointment__status__in=['confirmed', 'completed'])
                .exclude(appointments__status__in=['confirmed', 'completed'])
                .order_by("start_time")
            )

        # Range query: mentor_id + from + to
        elif from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except ValueError:
                return TimeSlot.objects.none()

            qs = (
                TimeSlot.objects
                .filter(
                    mentor_id=mentor_id,
                    start_time__date__gte=from_date,
                    start_time__date__lte=to_date,
                )
                .filter(availability_filter)
                .filter(
                    Q(reserved_until__isnull=True) | Q(reserved_until__lte=now)
                )
                .exclude(reserved_appointment__status__in=['confirmed', 'completed'])
                .exclude(appointments__status__in=['confirmed', 'completed'])
                .order_by("start_time")
            )

        # Neither pattern valid
        else:
            return TimeSlot.objects.none()

        # Exclude past time slots (applies to both single-day and range queries)
        # Use __gt (not __gte) to ensure only future slots are returned
        qs = qs.filter(start_time__gt=now)

        # Service duration safety (applies to both single-day and range queries)
        if service_id:
            try:
                from mentors.models import MentorService
                service = MentorService.objects.get(
                    id=service_id,
                    mentor_id=mentor_id,
                    is_active=True
                )
                qs = qs.filter(
                    end_time__gte=F('start_time') + timedelta(minutes=service.duration_minutes)
                )
            except MentorService.DoesNotExist:
                return TimeSlot.objects.none()

        # Enforce hourly slots
        qs = qs.filter(
            end_time=F('start_time') + timedelta(minutes=60)
        ).order_by('start_time')

        # Defensive invariant: check queryset is valid without forcing full evaluation
        # Use exists() check instead of all() to avoid loading all records
        if not qs.exists():
            # If queryset is empty, return empty queryset (not None)
            return TimeSlot.objects.none()

        return qs

class TimeSlotDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a time slot"""
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return TimeSlot.objects.filter(mentor=user.mentor_profile)
        return TimeSlot.objects.none()

class TimeSlotCreateView(generics.CreateAPIView):
    """Mentor creates time slot"""
    serializer_class = TimeSlotCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()

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
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel appointment"""
        appointment = self.get_object()
        
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
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """User rates appointment"""
        appointment = self.get_object()
        
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

        from mentors.models import MentorReview
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
                schedule_payout_for_appointment(appointment)

            return Response(AppointmentSerializer(appointment).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Mentor updates appointment status"""
        appointment = get_object_or_404(Appointment, pk=pk, mentor=request.user.mentor_profile)
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
                
                # Idempotency check: ensure only one review reminder per appointment
                if not Notification.objects.filter(
                    user=appointment.user,
                    notification_type='system_announcement',
                    related_appointment=appointment,
                    title='Please review your session'
                ).exists():
                    # TODO: This notification is intended to be sent 24h after completion
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
                schedule_payout_for_appointment(appointment)
            
            return Response(serializer.data)
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
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Mentor responds to appointment request"""
        appointment_request = self.get_object()
        
        if not hasattr(request.user, 'mentor_profile'):
            return Response(
                {"error": "Only mentors can respond to requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment_request.mentor != request.user.mentor_profile:
            return Response(
                {"error": "You can only respond to your own requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = request.data.get('response', '')
        status_action = request.data.get('status')  # 'accepted' or 'rejected'
        suggested_slots = request.data.get('suggested_time_slots', [])
        
        if status_action not in ['accepted', 'rejected']:
            return Response(
                {"error": "Status must be 'accepted' or 'rejected'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment_request.status = status_action
        appointment_request.mentor_response = response
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def lock_slot(request):
    """
    Atomically lock a time slot and create a pending appointment.
    Also supports cancel and reschedule flows.

    Rules (Scheme A):
    1. Slot can be locked for 10 minutes.
    2. If lock expired -> release slot + expire appointment.
    3. If slot is locked and NOT expired:
        - Same user: reuse existing appointment (idempotent).
        - Different user: 409 Conflict.
    4. Expired appointments must NEVER keep slot locked.
    """

    appointment_id = request.data.get('appointment_id')
    action = request.data.get('action')
    time_slot_id = request.data.get('time_slot_id')
    service_id = request.data.get('service_id')
    title = request.data.get('title', '')
    description = request.data.get('description', '')

    # ------------------------------------------------------------------
    # CANCEL FLOW
    # ------------------------------------------------------------------
    if appointment_id and action == 'cancel':
        try:
            with transaction.atomic():
                appointment = Appointment.objects.select_for_update().get(
                    id=appointment_id,
                    user=request.user
                )
                cancel_reason = request.data.get('cancel_reason', '')
                
                if appointment.status not in ['pending', 'confirmed']:
                    return Response(
                        {'error': 'Only pending or confirmed appointments can be cancelled'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                old_slot = appointment.time_slot
                appointment.status = 'cancelled'
                appointment.cancelled_by = 'user'
                if cancel_reason:
                    appointment.cancellation_reason = cancel_reason
                    appointment.save(update_fields=['status', 'cancelled_by', 'cancellation_reason'])
                else:
                    appointment.save(update_fields=['status', 'cancelled_by'])

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

                if old_slot:
                    old_slot.is_available = True
                    old_slot.reserved_until = None
                    old_slot.reserved_appointment = None
                    old_slot.save(update_fields=['is_available', 'reserved_until', 'reserved_appointment'])
                    _sync_slot_bookings(old_slot)
                    _sync_slot_bookings(old_slot)
                
                return Response({
                    'appointment': {
                        'id': appointment.id,
                        'status': appointment.status,
                        'is_paid': appointment.is_paid,
                        'scheduled_start': appointment.scheduled_start,
                        'scheduled_end': appointment.scheduled_end,
                        'time_slot_id': old_slot.id if old_slot else None,
                        'mentor_id': appointment.mentor.id,
                        'price': str(appointment.price),
                        'currency': appointment.currency,
                    }
                }, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # ------------------------------------------------------------------
    # RESCHEDULE FLOW
    # ------------------------------------------------------------------
    if appointment_id and time_slot_id and service_id:
        try:
            from mentors.models import MentorService
            
            service = MentorService.objects.get(id=service_id)
            if not service.is_active:
                return Response(
                    {'error': 'Service is not active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except MentorService.DoesNotExist:
            return Response(
                {'error': 'Service not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                appointment = Appointment.objects.select_for_update().get(
                    id=appointment_id,
                    user=request.user
                )
                
                old_slot = appointment.time_slot
                old_details = appointment.get_notification_details()
                
                new_slot = TimeSlot.objects.select_for_update().get(id=time_slot_id)
                
                if service.mentor_id != new_slot.mentor_id:
                    return Response(
                        {'error': 'Service does not belong to this mentor'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if new_slot.mentor_id != appointment.mentor_id:
                    return Response(
                        {'error': 'Cannot reschedule to a different mentor'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                scheduled_start = new_slot.start_time
                scheduled_end = scheduled_start + timedelta(minutes=service.duration_minutes)
                
                if scheduled_end > new_slot.end_time:
                    return Response(
                        {'error': 'Service duration exceeds available slot'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if old_slot:
                    old_slot.is_available = True
                    old_slot.reserved_until = None
                    old_slot.reserved_appointment = None
                    old_slot.save(update_fields=['is_available', 'reserved_until', 'reserved_appointment'])
                
                now = timezone.now()
                appointment.time_slot = new_slot
                appointment.scheduled_start = scheduled_start
                appointment.scheduled_end = scheduled_end
                appointment.service_id = service_id

                if appointment.status == 'confirmed' and appointment.is_paid:
                    appointment.status = 'confirmed'
                else:
                    appointment.status = 'pending'

                appointment.save(update_fields=['time_slot', 'scheduled_start', 'scheduled_end', 'status', 'service'])

                new_slot.is_available = False
                if appointment.status == 'confirmed' and appointment.is_paid:
                    new_slot.reserved_until = None
                else:
                    new_slot.reserved_until = now + timedelta(minutes=10)
                new_slot.reserved_appointment = appointment
                new_slot.save(update_fields=['is_available', 'reserved_until', 'reserved_appointment'])
                _sync_slot_bookings(new_slot)

                mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
                appointment_details = appointment.get_notification_details()
                notify(
                    NotificationType.APPOINTMENT_RESCHEDULED,
                    context={
                        'appointment_id': appointment.id,
                        'student': appointment.user,
                        'mentor': appointment.mentor.user,
                    },
                    title='Appointment rescheduled',
                    message=(
                        f'Appointment rescheduled from {old_details} to {appointment_details} '
                        f'with {mentor_name}.'
                    ),
                    priority='normal',
                    related_appointment=appointment,
                    payload=appointment.get_notification_payload(),
                )
                
                return Response({
                    'appointment': {
                        'id': appointment.id,
                        'status': appointment.status,
                        'is_paid': appointment.is_paid,
                        'scheduled_start': appointment.scheduled_start,
                        'scheduled_end': appointment.scheduled_end,
                        'time_slot_id': new_slot.id,
                        'mentor_id': appointment.mentor.id,
                        'price': str(appointment.price),
                        'currency': appointment.currency,
                    },
                    'expires_at': new_slot.reserved_until.isoformat() if new_slot.reserved_until else None,
                }, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except TimeSlot.DoesNotExist:
            return Response(
                {'error': 'Time slot not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    # ------------------------------------------------------------------
    # CREATE FLOW (existing logic)
    # ------------------------------------------------------------------
    if not time_slot_id:
        return Response(
            {'error': 'time_slot_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not service_id:
        return Response(
            {'error': 'service_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    now = timezone.now()

    try:
        from mentors.models import MentorService
        
        service = MentorService.objects.get(id=service_id)
        if not service.is_active:
            return Response(
                {'error': 'Service is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except MentorService.DoesNotExist:
        return Response(
            {'error': 'Service not found'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            slot = TimeSlot.objects.select_for_update().get(id=time_slot_id)
            
            if service.mentor_id != slot.mentor_id:
                return Response(
                    {'error': 'Service does not belong to this mentor'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------------------------------------------------------
            # STEP 0: Handle locked slots without an active hold
            # ------------------------------------------------------------------
            if not slot.is_available and slot.reserved_until is None:
                if Appointment.objects.filter(
                    time_slot=slot,
                    status__in=['confirmed', 'completed']
                ).exists():
                    return Response(
                        {'error': 'This time slot is already booked'},
                        status=status.HTTP_409_CONFLICT
                    )
                existing_appt = slot.reserved_appointment
                if existing_appt and existing_appt.status in ['confirmed', 'completed']:
                    return Response(
                        {'error': 'This time slot is already booked'},
                        status=status.HTTP_409_CONFLICT
                    )
                if existing_appt and existing_appt.status in ['expired', 'cancelled']:
                    slot.is_available = True
                    slot.reserved_until = None
                    slot.reserved_appointment = None
                    slot.save(update_fields=[
                        'is_available',
                        'reserved_until',
                        'reserved_appointment',
                    ])
                elif existing_appt is None:
                    slot.is_available = True
                    slot.save(update_fields=['is_available'])

            # ------------------------------------------------------------------
            # STEP 1: If slot has a lock but it's expired → HARD RELEASE
            # ------------------------------------------------------------------
            if slot.reserved_until and slot.reserved_until <= now:
                if slot.reserved_appointment:
                    slot.reserved_appointment.status = 'expired'
                    slot.reserved_appointment.save(update_fields=['status'])

                slot.is_available = True
                slot.reserved_until = None
                slot.reserved_appointment = None
                slot.save(update_fields=[
                    'is_available',
                    'reserved_until',
                    'reserved_appointment',
                ])

            # ------------------------------------------------------------------
            # STEP 2: Slot still locked (not expired)
            # ------------------------------------------------------------------
            if slot.reserved_until and slot.reserved_until > now:
                existing_appt = slot.reserved_appointment

                # Safety check (should not happen, but defensive)
                if not existing_appt:
                    slot.is_available = True
                    slot.reserved_until = None
                    slot.reserved_appointment = None
                    slot.save(update_fields=['is_available', 'reserved_until', 'reserved_appointment'])
                else:
                    # Same user → idempotent retry (frontend refresh / back button)
                    if existing_appt.user_id == request.user.id:
                        return Response({
                            'appointment': {
                                'id': existing_appt.id,
                                'status': existing_appt.status,
                                'is_paid': existing_appt.is_paid,
                                'scheduled_start': existing_appt.scheduled_start,
                                'scheduled_end': existing_appt.scheduled_end,
                                'time_slot_id': slot.id,
                                'mentor_id': slot.mentor.id,
                                'price': str(existing_appt.price),
                                'currency': existing_appt.currency,
                            },
                            'expires_at': slot.reserved_until.isoformat(),
                        }, status=status.HTTP_200_OK)

                    # Different user → hard block
                    return Response(
                        {'error': 'This time slot is currently locked by another user'},
                        status=status.HTTP_409_CONFLICT
                    )

            if slot.current_bookings >= slot.max_bookings:
                return Response(
                    {'error': 'This time slot is fully booked'},
                    status=status.HTTP_409_CONFLICT
                )

            # ------------------------------------------------------------------
            # STEP 3: Slot is free → clean old junk + create new appointment
            # ------------------------------------------------------------------
            Appointment.objects.filter(
                time_slot=slot,
                status='pending',
                is_paid=False
            ).update(status='expired')

            scheduled_start = slot.start_time
            scheduled_end = scheduled_start + timedelta(minutes=service.duration_minutes)
            
            if scheduled_end > slot.end_time:
                return Response(
                    {'error': 'Service duration exceeds available slot'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            appointment = Appointment.objects.create(
                user=request.user,
                mentor=slot.mentor,
                time_slot=slot,
                service_id=service_id,
                title=title or f"Session with {slot.mentor.user.get_full_name() or slot.mentor.user.username}",
                description=description,
                status='pending',
                is_paid=False,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                price=slot.price,
                currency=slot.currency,
            )

            slot.is_available = False
            slot.reserved_until = now + timedelta(minutes=10)
            slot.reserved_appointment = appointment
            slot.save(update_fields=[
                'is_available',
                'reserved_until',
                'reserved_appointment',
            ])

            return Response({
                'appointment': {
                    'id': appointment.id,
                    'status': appointment.status,
                    'is_paid': appointment.is_paid,
                    'scheduled_start': appointment.scheduled_start,
                    'scheduled_end': appointment.scheduled_end,
                    'time_slot_id': slot.id,
                    'mentor_id': slot.mentor.id,
                    'price': str(appointment.price),
                    'currency': appointment.currency,
                },
                'expires_at': slot.reserved_until.isoformat(),
            }, status=status.HTTP_201_CREATED)

    except TimeSlot.DoesNotExist:
        return Response(
            {'error': 'Time slot not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def appointment_lock_status(request, appointment_id):
    from appointments.models import Appointment
    from django.utils import timezone

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        user=request.user
    )

    slot = appointment.time_slot
    now = timezone.now()

    expired = False
    seconds_left = 0

    if slot and slot.reserved_until:
        if now >= slot.reserved_until:
            expired = True

            # Core: automatically fix dirty status
            if appointment.status == 'pending':
                appointment.status = 'expired'
                appointment.save(update_fields=['status'])

            slot.is_available = True
            slot.reserved_until = None
            slot.reserved_appointment = None
            slot.save(update_fields=[
                'is_available',
                'reserved_until',
                'reserved_appointment',
            ])
        else:
            seconds_left = int((slot.reserved_until - now).total_seconds())

    return Response({
        'appointment_id': appointment.id,
        'appointment_status': appointment.status,
        'slot_id': slot.id if slot else None,
        'is_slot_available': slot.is_available if slot else None,
        'reserved_until': slot.reserved_until,
        'expired': expired,
        'seconds_left': seconds_left,
    })
