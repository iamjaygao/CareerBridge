from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from .models import TimeSlot, Appointment, AppointmentRequest
from .serializers import (
    TimeSlotSerializer, AppointmentSerializer, AppointmentRequestSerializer,
    AppointmentUpdateSerializer, TimeSlotCreateSerializer
)
from notifications.models import Notification

class TimeSlotListView(generics.ListAPIView):
    """Get available time slot list"""
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = TimeSlot.objects.filter(is_available=True, start_time__gt=timezone.now())
        
        # Filter by mentor
        mentor_id = self.request.query_params.get('mentor_id')
        if mentor_id:
            queryset = queryset.filter(mentor_id=mentor_id)
        
        # Filter by date
        date = self.request.query_params.get('date')
        if date:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    start_time__date=target_date
                )
            except ValueError:
                pass
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset.order_by('start_time')

class TimeSlotDetailView(generics.RetrieveAPIView):
    """Get time slot details"""
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by time
        upcoming = self.request.query_params.get('upcoming')
        if upcoming == 'true':
            queryset = queryset.filter(
                scheduled_start__gt=timezone.now(),
                status__in=['pending', 'confirmed']
            )
        elif upcoming == 'false':
            queryset = queryset.filter(scheduled_end__lt=timezone.now())
        
        return queryset.order_by('-created_at')
    
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
        
        mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
        appointment_datetime = appointment.scheduled_start.strftime('%Y-%m-%d %H:%M')
        Notification.objects.create(
            user=appointment.user,
            notification_type='appointment_cancelled',
            title='Appointment status updated',
            message=f'Appointment with {mentor_name} on {appointment_datetime} has been cancelled',
            priority='high',
            related_appointment=appointment
        )
        Notification.objects.create(
            user=appointment.mentor.user,
            notification_type='appointment_cancelled',
            title='Appointment status updated',
            message=f'Appointment with {appointment.user.get_full_name() or appointment.user.username} on {appointment_datetime} has been cancelled',
            priority='high',
            related_appointment=appointment
        )
        
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
        
        Notification.objects.create(
            user=appointment.mentor.user,
            notification_type='system_announcement',
            title='You received a new review',
            message=f'You received a {rating}-star review for your appointment on {appointment.scheduled_start.strftime("%Y-%m-%d %H:%M")}',
            priority='low',
            related_appointment=appointment
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
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Mentor updates appointment status"""
        appointment = get_object_or_404(Appointment, pk=pk, mentor=request.user.mentor_profile)
        old_status = appointment.status
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            appointment.refresh_from_db()
            
            if appointment.status in ['confirmed', 'cancelled', 'completed'] and appointment.status != old_status:
                mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
                student_name = appointment.user.get_full_name() or appointment.user.username
                appointment_datetime = appointment.scheduled_start.strftime('%Y-%m-%d %H:%M')
                notification_type = 'appointment_cancelled' if appointment.status == 'cancelled' else 'appointment_confirmed'
                priority = 'high' if appointment.status == 'cancelled' else 'normal'
                status_text = appointment.get_status_display()
                
                Notification.objects.create(
                    user=appointment.user,
                    notification_type=notification_type,
                    title='Appointment status updated',
                    message=f'{mentor_name} updated your appointment on {appointment_datetime} to {status_text}',
                    priority=priority,
                    related_appointment=appointment
                )
                Notification.objects.create(
                    user=appointment.mentor.user,
                    notification_type=notification_type,
                    title='Appointment status updated',
                    message=f'Your appointment with {student_name} on {appointment_datetime} is now {status_text}',
                    priority=priority,
                    related_appointment=appointment
                )
            
            if appointment.status == 'completed' and old_status != 'completed':
                mentor_name = appointment.mentor.user.get_full_name() or appointment.mentor.user.username
                appointment_datetime = appointment.scheduled_start.strftime('%Y-%m-%d %H:%M')
                
                # Idempotency check: ensure only one review reminder per appointment
                if not Notification.objects.filter(
                    user=appointment.user,
                    notification_type='system_announcement',
                    related_appointment=appointment,
                    title='Please review your session'
                ).exists():
                    # TODO: This notification is intended to be sent 24h after completion
                    Notification.objects.create(
                        user=appointment.user,
                        notification_type='system_announcement',
                        title='Please review your session',
                        message=f'Please share your feedback about your session with {mentor_name} on {appointment_datetime}',
                        priority='normal',
                        related_appointment=appointment,
                        sent_at=None,
                        payload={'action': 'review_appointment', 'appointment_id': appointment.id}
                    )
            
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
        appointment_request = serializer.save()
        student_name = appointment_request.user.get_full_name() or appointment_request.user.username
        Notification.objects.create(
            user=appointment_request.mentor.user,
            notification_type='mentor_response',
            title='New appointment request',
            message=f'You received a new appointment request from {student_name}',
            priority='normal'
        )

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
        status_text = 'accepted' if status_action == 'accepted' else 'rejected'
        Notification.objects.create(
            user=appointment_request.user,
            notification_type='mentor_response',
            title='Mentor responded to your request',
            message=f'{mentor_name} {status_text} your appointment request',
            priority='normal',
            related_mentor=appointment_request.mentor
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
