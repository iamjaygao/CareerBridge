from rest_framework import serializers
from .models import TimeSlot, Appointment, AppointmentRequest
from mentors.serializers import MentorProfileSerializer
from users.serializers import UserSerializer

class TimeSlotSerializer(serializers.ModelSerializer):
    """Time slot serializer"""
    
    mentor = MentorProfileSerializer(read_only=True)
    mentor_id = serializers.IntegerField(write_only=True)
    is_bookable = serializers.ReadOnlyField()
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'mentor', 'mentor_id', 'start_time', 'end_time', 'is_available',
            'is_recurring', 'recurring_pattern', 'max_bookings', 'current_bookings',
            'price', 'currency', 'is_bookable', 'duration_minutes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'current_bookings']

class AppointmentSerializer(serializers.ModelSerializer):
    """Appointment serializer"""
    
    user = UserSerializer(read_only=True)
    mentor = MentorProfileSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)
    time_slot_id = serializers.IntegerField(write_only=True)
    
    # Computed properties
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'mentor', 'time_slot', 'time_slot_id', 'title', 'description',
            'status', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end',
            'price', 'currency', 'is_paid', 'payment_method', 'meeting_link',
            'meeting_platform', 'meeting_notes', 'user_rating', 'user_feedback',
            'mentor_rating', 'mentor_feedback', 'cancellation_reason', 'cancelled_by',
            'cancellation_fee', 'refund_amount', 'is_upcoming', 'is_past', 'can_cancel',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'mentor', 'time_slot', 'created_at', 'updated_at',
            'actual_start', 'actual_end', 'cancellation_reason', 'cancelled_by',
            'cancellation_fee', 'refund_amount'
        ]
    
    def validate_time_slot_id(self, value):
        """Validate if time slot is available"""
        try:
            time_slot = TimeSlot.objects.get(id=value)
            if not time_slot.is_bookable:
                raise serializers.ValidationError("This time slot is not available for booking")
            return value
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("Time slot does not exist")
    
    def validate(self, data):
        """Validate appointment data"""
        # Check if time slot is available
        time_slot = TimeSlot.objects.get(id=data['time_slot_id'])
        
        # Check if user has conflicting appointments
        user = self.context['request'].user
        conflicting_appointments = Appointment.objects.filter(
            user=user,
            status__in=['pending', 'confirmed'],
            scheduled_start__lt=time_slot.end_time,
            scheduled_end__gt=time_slot.start_time
        )
        
        if conflicting_appointments.exists():
            raise serializers.ValidationError("You have a conflicting appointment at this time")
        
        # Set price
        data['price'] = time_slot.price
        data['currency'] = time_slot.currency
        data['scheduled_start'] = time_slot.start_time
        data['scheduled_end'] = time_slot.end_time
        
        return data
    
    def create(self, validated_data):
        """Create appointment"""
        time_slot_id = validated_data.pop('time_slot_id')
        time_slot = TimeSlot.objects.get(id=time_slot_id)
        
        # Create appointment
        appointment = Appointment.objects.create(
            user=self.context['request'].user,
            mentor=time_slot.mentor,
            time_slot=time_slot,
            **validated_data
        )
        
        # Update time slot booking count
        time_slot.current_bookings += 1
        time_slot.save()
        
        return appointment

class AppointmentRequestSerializer(serializers.ModelSerializer):
    """Appointment request serializer"""
    
    user = UserSerializer(read_only=True)
    mentor = MentorProfileSerializer(read_only=True)
    mentor_id = serializers.IntegerField(write_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = AppointmentRequest
        fields = [
            'id', 'user', 'mentor', 'mentor_id', 'preferred_date', 'preferred_time_start',
            'preferred_time_end', 'alternative_dates', 'title', 'description', 'topics',
            'status', 'mentor_response', 'suggested_time_slots', 'is_expired',
            'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'user', 'mentor', 'status', 'mentor_response', 'suggested_time_slots',
            'created_at', 'updated_at', 'expires_at'
        ]
    
    def validate_mentor_id(self, value):
        """Validate if mentor exists"""
        from mentors.models import MentorProfile
        try:
            MentorProfile.objects.get(id=value)
            return value
        except MentorProfile.DoesNotExist:
            raise serializers.ValidationError("Mentor does not exist")
    
    def validate(self, data):
        """Validate appointment request data"""
        # Check if preferred time is in the future
        from django.utils import timezone
        from datetime import datetime
        
        preferred_datetime = datetime.combine(
            data['preferred_date'], 
            data['preferred_time_start']
        )
        
        if preferred_datetime <= timezone.now():
            raise serializers.ValidationError("Preferred time must be in the future")
        
        # Check if end time is later than start time
        if data['preferred_time_end'] <= data['preferred_time_start']:
            raise serializers.ValidationError("End time must be after start time")
        
        return data
    
    def create(self, validated_data):
        """Create appointment request"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Set expiration time (7 days later)
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        
        return AppointmentRequest.objects.create(
            user=self.context['request'].user,
            **validated_data
        )

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Appointment update serializer (for mentor status updates)"""
    
    class Meta:
        model = Appointment
        fields = [
            'status', 'meeting_link', 'meeting_platform', 'meeting_notes',
            'mentor_rating', 'mentor_feedback'
        ]
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        if instance:
            # Check if status transition is valid
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'completed': [],
                'cancelled': [],
                'no_show': []
            }
            
            current_status = instance.status
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(f"Cannot transition from {current_status} to {value}")
        
        return value

class TimeSlotCreateSerializer(serializers.ModelSerializer):
    """Time slot creation serializer (for mentor to create available times)"""
    
    class Meta:
        model = TimeSlot
        fields = [
            'start_time', 'end_time', 'is_available', 'is_recurring', 'recurring_pattern',
            'max_bookings', 'price', 'currency'
        ]
    
    def validate(self, data):
        """Validate time slot data"""
        from django.utils import timezone
        
        # Check if time is in the future
        if data['start_time'] <= timezone.now():
            raise serializers.ValidationError("Start time must be in the future")
        
        # Check if end time is later than start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        # Check for time conflicts
        mentor = self.context['request'].user.mentor_profile
        conflicting_slots = TimeSlot.objects.filter(
            mentor=mentor,
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time']
        )
        
        if conflicting_slots.exists():
            raise serializers.ValidationError("Time slot conflicts with existing availability")
        
        return data
    
    def create(self, validated_data):
        """Create time slot"""
        mentor = self.context['request'].user.mentor_profile
        return TimeSlot.objects.create(mentor=mentor, **validated_data) 