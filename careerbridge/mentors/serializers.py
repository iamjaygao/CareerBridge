from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MentorProfile, MentorService, MentorAvailability, MentorSession,
    MentorReview, MentorApplication, MentorPayment, MentorNotification
)
from .services import MentorRecommendationService, MentorSearchService, MentorAnalyticsService

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for mentor profiles"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar')
        ref_name = "MentorUserSerializer"

class MentorProfileSerializer(serializers.ModelSerializer):
    """Mentor profile serializer"""
    user = UserSerializer(read_only=True)
    ranking_score = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    
    class Meta:
        model = MentorProfile
        fields = (
            'id', 'user', 'bio', 'years_of_experience', 'current_position', 'industry',
            'status', 'average_rating', 'total_reviews', 'total_sessions', 'total_earnings',
            'is_verified', 'verification_badge', 'specializations', 'ranking_score',
            'is_approved', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'status', 'average_rating', 'total_reviews', 'total_sessions', 
            'total_earnings', 'is_verified', 'verification_badge', 'ranking_score',
            'created_at', 'updated_at'
        )

class MentorProfileDetailSerializer(MentorProfileSerializer):
    """Detailed mentor profile serializer with payment info"""
    stripe_account_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    paypal_email = serializers.EmailField(required=False, allow_blank=True)
    bank_account_info = serializers.JSONField(required=False)
    
    class Meta(MentorProfileSerializer.Meta):
        fields = MentorProfileSerializer.Meta.fields + (
            'stripe_account_id', 'paypal_email', 'bank_account_info'
        )

class MentorDetailSerializer(MentorProfileSerializer):
    """Comprehensive mentor detail serializer with services, reviews, and availability"""
    services = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    
    class Meta(MentorProfileSerializer.Meta):
        fields = MentorProfileSerializer.Meta.fields + ('services', 'reviews', 'availability')
    
    def get_services(self, obj):
        """Get mentor's active services"""
        services = obj.services.filter(is_active=True)
        return MentorServiceSerializer(services, many=True).data
    
    def get_reviews(self, obj):
        """Get mentor's recent reviews"""
        reviews = obj.reviews.all()[:10]  # Limit to 10 most recent reviews
        return MentorReviewSerializer(reviews, many=True).data
    
    def get_availability(self, obj):
        """Get mentor's availability"""
        availability = obj.availabilities.filter(is_active=True)
        return MentorAvailabilitySerializer(availability, many=True).data

class MentorServiceSerializer(serializers.ModelSerializer):
    """Mentor service serializer"""
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    display_price = serializers.ReadOnlyField()
    
    class Meta:
        model = MentorService
        fields = (
            'id', 'mentor', 'service_type', 'title', 'description',
            'pricing_model', 'price_per_hour', 'fixed_price', 'package_price',
            'package_sessions', 'duration_minutes', 'platform_fee_percentage',
            'mentor_earnings_percentage', 'display_price', 'is_active',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

class MentorAvailabilitySerializer(serializers.ModelSerializer):
    """Mentor availability serializer"""
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = MentorAvailability
        fields = ('id', 'mentor', 'day_of_week', 'start_time', 'end_time', 'is_active')
    
    def validate(self, data):
        """Validate availability times"""
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data

class MentorSessionSerializer(serializers.ModelSerializer):
    """Mentor session serializer"""
    mentor = MentorProfileSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    service = MentorServiceSerializer(read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = MentorSession
        fields = (
            'id', 'mentor', 'user', 'service', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'status', 'user_notes', 'mentor_notes',
            'session_feedback', 'meeting_link', 'meeting_platform', 'is_upcoming',
            'created_at', 'updated_at', 'completed_at'
        )
        read_only_fields = ('mentor', 'user', 'created_at', 'updated_at', 'completed_at')

class MentorSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new sessions"""
    mentor_id = serializers.IntegerField(write_only=True)
    service_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MentorSession
        fields = (
            'mentor_id', 'service_id', 'scheduled_date', 'scheduled_time',
            'duration_minutes', 'user_notes'
        )
    
    def validate(self, data):
        """Validate session booking"""
        mentor = MentorProfile.objects.get(id=data['mentor_id'])
        service = MentorService.objects.get(id=data['service_id'])
        
        # Check if mentor is approved
        if not mentor.is_approved:
            raise serializers.ValidationError("Mentor is not approved")
        
        # Check if service belongs to mentor
        if service.mentor != mentor:
            raise serializers.ValidationError("Service does not belong to this mentor")
        
        # Check availability
        day_of_week = data['scheduled_date'].weekday()
        availability = MentorAvailability.objects.filter(
            mentor=mentor,
            day_of_week=day_of_week,
            start_time__lte=data['scheduled_time'],
            end_time__gt=data['scheduled_time'],
            is_active=True
        ).first()
        
        if not availability:
            raise serializers.ValidationError("Mentor is not available at this time")
        
        # Check for conflicts
        conflicting_sessions = MentorSession.objects.filter(
            mentor=mentor,
            scheduled_date=data['scheduled_date'],
            scheduled_time=data['scheduled_time'],
            status__in=['pending', 'confirmed']
        )
        
        if conflicting_sessions.exists():
            raise serializers.ValidationError("This time slot is already booked")
        
        return data
    
    def create(self, validated_data):
        """Create session with mentor and service"""
        mentor_id = validated_data.pop('mentor_id')
        service_id = validated_data.pop('service_id')
        
        mentor = MentorProfile.objects.get(id=mentor_id)
        service = MentorService.objects.get(id=service_id)
        
        return MentorSession.objects.create(
            mentor=mentor,
            service=service,
            user=self.context['request'].user,
            **validated_data
        )

class MentorReviewSerializer(serializers.ModelSerializer):
    """Mentor review serializer"""
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    user = UserSerializer(read_only=True)
    session = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = MentorReview
        fields = (
            'id', 'mentor', 'user', 'session', 'rating', 'comment',
            'created_at', 'updated_at'
        )
        read_only_fields = ('mentor', 'user', 'created_at', 'updated_at')
    
    def validate_rating(self, value):
        """Validate rating value"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate(self, data):
        """Validate review submission"""
        mentor = self.context.get('mentor')
        user = self.context['request'].user
        
        # Check if user has already reviewed this mentor
        existing_review = MentorReview.objects.filter(
            mentor=mentor,
            user=user
        ).first()
        
        if existing_review:
            raise serializers.ValidationError("You have already reviewed this mentor")
        
        return data
    
    def create(self, validated_data):
        """Create review with mentor and user"""
        mentor = self.context.get('mentor')
        user = self.context['request'].user
        
        return MentorReview.objects.create(
            mentor=mentor,
            user=user,
            **validated_data
        )

class MentorApplicationSerializer(serializers.ModelSerializer):
    """Mentor application serializer"""
    user = UserSerializer(read_only=True)
    status = serializers.ReadOnlyField()
    reviewed_by = UserSerializer(read_only=True)
    reviewed_at = serializers.ReadOnlyField()
    
    class Meta:
        model = MentorApplication
        fields = (
            'id', 'user', 'motivation', 'relevant_experience',
            'preferred_payment_method', 'status', 'review_notes',
            'reviewed_by', 'reviewed_at', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'status', 'review_notes', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create application with current user"""
        user = self.context['request'].user
        
        # Check if user already has an application
        existing_application = MentorApplication.objects.filter(user=user).first()
        if existing_application:
            raise serializers.ValidationError("You already have a pending application")
        
        # Check if user is already a mentor
        if hasattr(user, 'mentor_profile'):
            raise serializers.ValidationError("You are already a mentor")
        
        return MentorApplication.objects.create(user=user, **validated_data)

class MentorPaymentSerializer(serializers.ModelSerializer):
    """Mentor payment serializer"""
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    session = MentorSessionSerializer(read_only=True)
    
    class Meta:
        model = MentorPayment
        fields = (
            'id', 'mentor', 'session', 'total_amount', 'platform_fee',
            'mentor_earnings', 'tax_amount', 'payment_method', 'transaction_id',
            'payment_status', 'refund_amount', 'refund_reason', 'refunded_at',
            'created_at', 'processed_at'
        )
        read_only_fields = (
            'mentor', 'session', 'total_amount', 'platform_fee', 'mentor_earnings',
            'tax_amount', 'transaction_id', 'payment_status', 'refund_amount',
            'refund_reason', 'refunded_at', 'created_at', 'processed_at'
        )

class MentorNotificationSerializer(serializers.ModelSerializer):
    """Mentor notification serializer"""
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    related_session = serializers.PrimaryKeyRelatedField(read_only=True)
    related_payment = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = MentorNotification
        fields = (
            'id', 'mentor', 'notification_type', 'title', 'message',
            'is_read', 'is_sent', 'related_session', 'related_payment',
            'created_at', 'read_at'
        )
        read_only_fields = ('mentor', 'notification_type', 'title', 'message', 'is_sent', 'created_at', 'read_at')

class MentorSearchSerializer(serializers.Serializer):
    """Serializer for mentor search parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    service_type = serializers.ChoiceField(
        choices=MentorService.SERVICE_TYPE_CHOICES,
        required=False
    )
    industry = serializers.CharField(required=False, allow_blank=True)
    min_rating = serializers.FloatField(required=False, min_value=1.0, max_value=5.0)
    max_price = serializers.DecimalField(required=False, max_digits=8, decimal_places=2)
    is_verified = serializers.BooleanField(required=False)
    availability_day = serializers.IntegerField(required=False, min_value=0, max_value=6)
    availability_time = serializers.TimeField(required=False)

class MentorRecommendationSerializer(serializers.Serializer):
    """Serializer for mentor recommendations"""
    service_type = serializers.ChoiceField(
        choices=MentorService.SERVICE_TYPE_CHOICES,
        required=False
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=50, default=10)

class MentorAnalyticsSerializer(serializers.Serializer):
    """Serializer for mentor analytics"""
    days = serializers.IntegerField(required=False, min_value=1, max_value=365, default=30)

class MentorAvailabilitySlotSerializer(serializers.Serializer):
    """Serializer for availability slots"""
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_available = serializers.BooleanField()
    duration_minutes = serializers.IntegerField()

class MentorRankingSerializer(serializers.Serializer):
    """Serializer for mentor rankings"""
    ranking_type = serializers.ChoiceField(
        choices=[
            ('rating', 'By Rating'),
            ('sessions', 'By Sessions'),
            ('earnings', 'By Earnings'),
            ('overall', 'Overall Ranking')
        ],
        default='overall'
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)
    category = serializers.ChoiceField(
        choices=MentorService.SERVICE_TYPE_CHOICES,
        required=False
    )
    industry = serializers.CharField(required=False, allow_blank=True) 