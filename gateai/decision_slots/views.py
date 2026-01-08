"""
decision_slots/views.py

KERNEL ARBITRATION LAYER - READ ONLY

This module provides:
1. TimeSlot resource management (read-only queries)
2. Slot locking arbitration (lock_slot syscall)
3. Lock status queries (appointment_lock_status)

STRICT RULES:
- NO Appointment domain CRUD (moved to appointments app)
- NO serializer.save() for Appointment domain logic
- lock_slot is a KERNEL SYSCALL for resource arbitration
- All appointment domain operations must go through appointments app
"""

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime, timedelta

from appointments.models import TimeSlot, Appointment, AppointmentRequest
from appointments.serializers import (
    TimeSlotSerializer, TimeSlotCreateSerializer
)
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from django.contrib.auth import get_user_model


# ============================================================================
# HELPER FUNCTIONS (KERNEL UTILITY)
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


def _notify_staff_appointment_cancelled(appointment) -> None:
    """Send notification to staff when appointment is cancelled (kernel event)"""
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


# ============================================================================
# TIMESLOT RESOURCE VIEWS (KERNEL RESOURCE MANAGEMENT - READ ONLY)
# ============================================================================

class TimeSlotListView(generics.ListAPIView):
    """
    Get available time slot list (KERNEL RESOURCE QUERY)
    
    FINAL TimeSlot provider.
    
    Contract:
    - Return ONLY real TimeSlot records
    - NO state mutation
    - NO availability inference
    """
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
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
                from human_loop.models import MentorService
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
    """Get or update a time slot (KERNEL RESOURCE MANAGEMENT)"""
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return TimeSlot.objects.filter(mentor=user.mentor_profile)
        return TimeSlot.objects.none()


class TimeSlotCreateView(generics.CreateAPIView):
    """Mentor creates time slot (KERNEL RESOURCE CREATION)"""
    serializer_class = TimeSlotCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()


# ============================================================================
# KERNEL ARBITRATION SYSCALLS
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def lock_slot(request):
    """
    KERNEL SYSCALL: Atomically lock a time slot and create a pending appointment.
    
    This is a KERNEL ARBITRATION function, not domain CRUD.
    It handles resource locking and creates appointments as part of the lock protocol.
    
    Supports flows:
    - CREATE: Lock slot + create pending appointment
    - CANCEL: Release lock + cancel appointment
    - RELEASE: Release lock + expire appointment (payment failure)
    - RESCHEDULE: Move lock to new slot
    
    Rules (Scheme A):
    1. Slot can be locked for 10 minutes.
    2. If lock expired → release slot + expire appointment.
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
    # RELEASE FLOW (payment failure / user abort)
    # ------------------------------------------------------------------
    if appointment_id and action == 'release':
        try:
            with transaction.atomic():
                appointment = Appointment.objects.select_for_update().get(
                    id=appointment_id,
                    user=request.user
                )
                slot = appointment.time_slot

                if appointment.status in ['cancelled', 'expired']:
                    return Response({
                        'appointment': {
                            'id': appointment.id,
                            'status': appointment.status,
                            'is_paid': appointment.is_paid,
                            'scheduled_start': appointment.scheduled_start,
                            'scheduled_end': appointment.scheduled_end,
                            'time_slot_id': slot.id if slot else None,
                            'mentor_id': appointment.mentor.id,
                            'price': str(appointment.price),
                            'currency': appointment.currency,
                        }
                    }, status=status.HTTP_200_OK)

                if appointment.is_paid or appointment.status in ['confirmed', 'completed']:
                    return Response(
                        {'error': 'Cannot release a paid or confirmed appointment'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                appointment.status = 'expired'
                appointment.cancelled_by = 'system'
                appointment.cancellation_reason = 'payment_failed'
                appointment.save(update_fields=['status', 'cancelled_by', 'cancellation_reason'])

                if slot:
                    slot.is_available = True
                    slot.reserved_until = None
                    slot.reserved_appointment = None
                    slot.save(update_fields=['is_available', 'reserved_until', 'reserved_appointment'])
                    _sync_slot_bookings(slot)

                return Response({
                    'appointment': {
                        'id': appointment.id,
                        'status': appointment.status,
                        'is_paid': appointment.is_paid,
                        'scheduled_start': appointment.scheduled_start,
                        'scheduled_end': appointment.scheduled_end,
                        'time_slot_id': slot.id if slot else None,
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
            from human_loop.models import MentorService
            
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
        from human_loop.models import MentorService
        
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
    """
    KERNEL QUERY: Check appointment lock status (minimal kernel state only)
    
    Returns:
    - appointment_id
    - appointment_status
    - slot_id
    - is_slot_available
    - reserved_until
    - expired
    - seconds_left
    
    NO UI-facing or domain data.
    """
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
