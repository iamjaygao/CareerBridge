from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from zoneinfo import ZoneInfo
from mentors.services import enrich_mentor_value_copy,build_mentor_contract


from .models import (
    MentorProfile,
    MentorService,
    MentorAvailability,
    MentorSession,
    MentorReview,
    MentorApplication,
    MentorPayment,
    MentorNotification,
)

from .services.legacy import (
    MentorRecommendationService,
    MentorSearchService,
    MentorAnalyticsService,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for mentor profiles"""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "avatar")
        # Avoid schema name collision across apps
        ref_name = "MentorUserSerializer"

class MentorProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    badge = serializers.SerializerMethodField()


    # SaaS system outputs
    system_insight = serializers.CharField(source='verification_badge', read_only=True)
    cta_label = serializers.SerializerMethodField()

    # Display
    headline = serializers.SerializerMethodField()

    ranking_reason = serializers.SerializerMethodField()

    # DB-backed price (single source of truth)
    starting_price = serializers.FloatField(read_only=True)

    # Frontend aliases
    job_title = serializers.CharField(source='current_position', read_only=True)
    expertise = serializers.JSONField(source='specializations', read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)
    review_count = serializers.IntegerField(source='total_reviews', read_only=True)

    class Meta:
        model = MentorProfile
        fields = (
            "id",
            "user",
            "bio",
            "badge",

            # Positioning (system controlled)
            "primary_track",
            "system_role",
            "primary_focus",
            "session_focus",

            # SaaS voice
            "system_insight",
            "cta_label",

            # Display
            "headline",
            "job_title",
            "industry",
            "expertise",
            "ranking_reason",

            # Pricing
            "starting_price",

            # Trust
            "rating",
            "review_count",
            "is_verified",
            "timezone",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 1) market-grade value copy
        data = enrich_mentor_value_copy(data)

        # 2) frozen v1 contract
        request = self.context.get("request")
        is_visitor = not bool(getattr(request, "user", None) and request.user.is_authenticated)
        data = build_mentor_contract(data)

        return data
    
    def get_badge(self, obj):
        """
        Platform-level mentor badge
        NOT user editable
        """
        average_rating = getattr(obj, 'average_rating', None)
        if obj.is_verified and average_rating and float(average_rating) >= 4.8:
            return "featured"

        total_reviews = getattr(obj, 'total_reviews', None)
        if total_reviews and total_reviews >= 20:
            return "top_pick"

        return None

    def get_headline(self, obj: MentorProfile) -> str:
        parts: list[str] = []
        if getattr(obj, "current_position", None):
            parts.append(obj.current_position)
        specs = getattr(obj, "specializations", None) or []
        if specs:
            parts.append(", ".join(specs[:2]))
        return " | ".join([p for p in parts if p]) or "Expert Mentor"
    
    def get_ranking_reason(self, obj: MentorProfile) -> str:
        """
        Explain WHY this mentor is ranked/recommended.
        This is for user trust & transparency (SaaS-grade).
        """
        if obj.total_sessions >= 50 and obj.average_rating >= 4.8:
            return "Top-rated mentor with extensive session experience"

        if obj.total_sessions >= 20:
            return "Frequently chosen by students"

        if obj.is_verified:
            return "Verified mentor on CareerBridge"

        if obj.primary_track:
            return "Recommended for your current career focus"

        return "Recommended based on profile match"

    def validate_timezone(self, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:
            raise serializers.ValidationError("Invalid timezone") from exc
        return value


    def get_starting_price(self, obj: MentorProfile):
        # Look for the cheapest active service
        services = obj.services.filter(is_active=True)
        if not services.exists():
            return 0.0
        prices = [float(s.price_per_hour or s.fixed_price or 0) for s in services]
        return min(prices) if prices else 0.0

    def get_hourly_rate(self, obj: MentorProfile):
        return self.get_starting_price(obj)
    
    def get_system_insight(self, obj):
        return self._build_system_insight(obj)

    def _build_system_insight(self, obj):
        rules = [
            (obj.total_sessions >= 50, "Frequently booked mentor"),
            (obj.total_sessions >= 10, "Popular among students"),
            (obj.is_verified, "Verified mentor on platform"),
        ]
        for condition, label in rules:
            if condition:
                return label
        return "New mentor on platform"


    def get_cta_label(self, obj: MentorProfile) -> str:
        if obj.primary_track == "resume_review":
            return "Start resume review"

        if obj.primary_track == "mock_interview":
            if obj.total_sessions >= 30:
                return "Practice with top interviewer"
            return "Prepare for interviews"

        if obj.primary_track == "career_switch":
            return "Begin career switch path"

        if obj.primary_track == "advanced_interview":
            return "Check readiness"

        return "See how this fits my plan"

class MentorProfilePaymentSerializer(MentorProfileSerializer):
    """
    Mentor profile serializer with payment fields.
    Use this ONLY for mentor settings / onboarding endpoints.
    """

    stripe_account_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    paypal_email = serializers.EmailField(required=False, allow_blank=True)
    bank_account_info = serializers.JSONField(required=False)

    class Meta(MentorProfileSerializer.Meta):
        fields = MentorProfileSerializer.Meta.fields + (
            "stripe_account_id",
            "paypal_email",
            "bank_account_info",
        )


class MentorServiceSerializer(serializers.ModelSerializer):
    """Mentor service serializer"""

    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    display_price = serializers.ReadOnlyField()

    class Meta:
        model = MentorService
        fields = (
            "id",
            "mentor",
            "service_type",
            "title",
            "description",
            "pricing_model",
            "price_per_hour",
            "fixed_price",
            "package_price",
            "package_sessions",
            "duration_minutes",
            "platform_fee_percentage",
            "mentor_earnings_percentage",
            "display_price",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class MentorAvailabilitySerializer(serializers.ModelSerializer):
    """Mentor availability serializer"""

    mentor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MentorAvailability
        fields = ("id", "mentor", "day_of_week", "start_time", "end_time", "is_active")

    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time")
        return data


class MentorReviewSerializer(serializers.ModelSerializer):
    """Mentor review serializer"""

    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    user = UserSerializer(read_only=True)
    session = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MentorReview
        fields = ("id", "mentor", "user", "session", "rating", "comment", "created_at", "updated_at")
        read_only_fields = ("mentor", "user", "created_at", "updated_at")

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):
        mentor = self.context.get("mentor")
        user = self.context["request"].user

        if mentor is None:
            # This serializer expects mentor in context for create
            return data

        existing_review = MentorReview.objects.filter(mentor=mentor, user=user).first()
        if existing_review:
            raise serializers.ValidationError("You have already reviewed this mentor")

        return data

    def create(self, validated_data):
        mentor = self.context.get("mentor")
        user = self.context["request"].user

        if mentor is None:
            raise serializers.ValidationError("Mentor context is required to create a review")

        return MentorReview.objects.create(mentor=mentor, user=user, **validated_data)


class MentorProfileDetailSerializer(MentorProfileSerializer):
    """Comprehensive mentor detail serializer with services, reviews, and availability"""

    services = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    primary_service_id = serializers.IntegerField(required=False, allow_null=True)
    current_position = serializers.CharField(required=False, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False)
    specializations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    class Meta(MentorProfileSerializer.Meta):
        fields = MentorProfileSerializer.Meta.fields + (
            "services",
            "reviews",
            "availability",
            "primary_service_id",
            "current_position",
            "years_of_experience",
            "specializations",
        )
    
    def validate_primary_service_id(self, value):
        """Validate that primary_service_id is a valid, active service belonging to this mentor"""
        if value is None:
            return value
        
        # Get the mentor from context (during update) or from instance (during read)
        mentor = self.instance if hasattr(self, 'instance') and self.instance else None
        
        # During create/update, check if service belongs to request user's mentor profile
        request = self.context.get('request')
        if request and request.user and hasattr(request.user, 'mentor_profile'):
            mentor = request.user.mentor_profile
        
        if not mentor:
            raise serializers.ValidationError("Unable to validate service: mentor profile not found")
        
        try:
            service = MentorService.objects.get(id=value, mentor=mentor, is_active=True)
        except MentorService.DoesNotExist:
            raise serializers.ValidationError(
                "Service does not exist, is not active, or does not belong to you"
            )
        
        return value
    
    def to_representation(self, instance):
        """Override to return validated primary_service_id in output and apply detail view contract"""
        data = super().to_representation(instance)
        
        # Validate that the stored primary_service_id is still valid
        primary_service_id = getattr(instance, 'primary_service_id', None)
        if primary_service_id:
            try:
                service = MentorService.objects.get(
                    id=primary_service_id,
                    mentor=instance,
                    is_active=True
                )
                data['primary_service_id'] = primary_service_id
            except MentorService.DoesNotExist:
                # Service no longer exists or is inactive - return None
                data['primary_service_id'] = None
        else:
            data['primary_service_id'] = None
        
        # Apply contract with is_detail_view=True for detail page
        request = self.context.get("request")
        is_visitor = not bool(getattr(request, "user", None) and request.user.is_authenticated)
        data = build_mentor_contract(data, is_detail_view=True)
        
        return data

    def get_services(self, obj):
        services = obj.services.filter(is_active=True)
        return MentorServiceSerializer(services, many=True).data

    def get_reviews(self, obj):
        reviews = obj.reviews.all()[:10]
        return MentorReviewSerializer(reviews, many=True).data

    def get_availability(self, obj):
        availability = obj.availabilities.filter(is_active=True)
        return MentorAvailabilitySerializer(availability, many=True).data


class MentorSessionSerializer(serializers.ModelSerializer):
    """Mentor session serializer"""

    mentor = MentorProfileSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    service = MentorServiceSerializer(read_only=True)
    is_upcoming = serializers.ReadOnlyField()

    class Meta:
        model = MentorSession
        fields = (
            "id",
            "mentor",
            "user",
            "service",
            "scheduled_date",
            "scheduled_time",
            "duration_minutes",
            "status",
            "user_notes",
            "mentor_notes",
            "session_feedback",
            "meeting_link",
            "meeting_platform",
            "is_upcoming",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = ("mentor", "user", "created_at", "updated_at", "completed_at")


class MentorSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new sessions"""

    mentor_id = serializers.IntegerField(write_only=True)
    service_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MentorSession
        fields = ("mentor_id", "service_id", "scheduled_date", "scheduled_time", "duration_minutes", "user_notes")

    def validate(self, data):
        mentor = MentorProfile.objects.get(id=data["mentor_id"])
        service = MentorService.objects.get(id=data["service_id"])

        if not getattr(mentor, "is_approved", False):
            raise serializers.ValidationError("Mentor is not approved")

        if service.mentor_id != mentor.id:
            raise serializers.ValidationError("Service does not belong to this mentor")

        # Availability check
        day_of_week = data["scheduled_date"].weekday()
        availability = MentorAvailability.objects.filter(
            mentor=mentor,
            day_of_week=day_of_week,
            start_time__lte=data["scheduled_time"],
            end_time__gt=data["scheduled_time"],
            is_active=True,
        ).first()

        if not availability:
            raise serializers.ValidationError("Mentor is not available at this time")

        # Conflict check (best-effort; true concurrency protection should be DB constraint / lock)
        conflicting_sessions = MentorSession.objects.filter(
            mentor=mentor,
            scheduled_date=data["scheduled_date"],
            scheduled_time=data["scheduled_time"],
            status__in=["pending", "confirmed"],
        )
        if conflicting_sessions.exists():
            raise serializers.ValidationError("This time slot is already booked")

        return data

    @transaction.atomic
    def create(self, validated_data):
        mentor_id = validated_data.pop("mentor_id")
        service_id = validated_data.pop("service_id")

        mentor = MentorProfile.objects.select_for_update().get(id=mentor_id)
        service = MentorService.objects.get(id=service_id)

        # Re-check conflicts inside transaction (reduces race risk)
        conflict = MentorSession.objects.select_for_update().filter(
            mentor=mentor,
            scheduled_date=validated_data["scheduled_date"],
            scheduled_time=validated_data["scheduled_time"],
            status__in=["pending", "confirmed"],
        )
        if conflict.exists():
            raise serializers.ValidationError("This time slot is already booked")

        return MentorSession.objects.create(
            mentor=mentor,
            service=service,
            user=self.context["request"].user,
            **validated_data,
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
            "id",
            "user",
            "motivation",
            "relevant_experience",
            "preferred_payment_method",
            "status",
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "user",
            "status",
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        user = self.context["request"].user

        existing_application = MentorApplication.objects.filter(user=user).first()
        if existing_application:
            raise serializers.ValidationError("You already have a pending application")

        if hasattr(user, "mentor_profile"):
            raise serializers.ValidationError("You are already a mentor")

        return MentorApplication.objects.create(user=user, **validated_data)


class MentorPaymentSerializer(serializers.ModelSerializer):
    """Mentor payment serializer"""

    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    session = MentorSessionSerializer(read_only=True)

    class Meta:
        model = MentorPayment
        fields = (
            "id",
            "mentor",
            "session",
            "total_amount",
            "platform_fee",
            "mentor_earnings",
            "tax_amount",
            "payment_method",
            "transaction_id",
            "payment_status",
            "refund_amount",
            "refund_reason",
            "refunded_at",
            "created_at",
            "processed_at",
        )
        read_only_fields = (
            "mentor",
            "session",
            "total_amount",
            "platform_fee",
            "mentor_earnings",
            "tax_amount",
            "transaction_id",
            "payment_status",
            "refund_amount",
            "refund_reason",
            "refunded_at",
            "created_at",
            "processed_at",
        )


class MentorNotificationSerializer(serializers.ModelSerializer):
    """Mentor notification serializer"""

    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    related_session = serializers.PrimaryKeyRelatedField(read_only=True)
    related_payment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MentorNotification
        fields = (
            "id",
            "mentor",
            "notification_type",
            "title",
            "message",
            "is_read",
            "is_sent",
            "related_session",
            "related_payment",
            "created_at",
            "read_at",
        )
        read_only_fields = (
            "mentor",
            "notification_type",
            "title",
            "message",
            "is_sent",
            "created_at",
            "read_at",
        )


class MentorSearchSerializer(serializers.Serializer):
    """Serializer for mentor search parameters"""

    query = serializers.CharField(required=False, allow_blank=True)
    service_type = serializers.ChoiceField(choices=MentorService.SERVICE_TYPE_CHOICES, required=False)
    industry = serializers.CharField(required=False, allow_blank=True)
    min_rating = serializers.FloatField(required=False, min_value=1.0, max_value=5.0)
    max_price = serializers.DecimalField(required=False, max_digits=8, decimal_places=2)
    is_verified = serializers.BooleanField(required=False)
    availability_day = serializers.IntegerField(required=False, min_value=0, max_value=6)
    availability_time = serializers.TimeField(required=False)


class MentorRecommendationSerializer(serializers.Serializer):
    """Serializer for mentor recommendations"""

    service_type = serializers.ChoiceField(choices=MentorService.SERVICE_TYPE_CHOICES, required=False)
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
            ("rating", "By Rating"),
            ("sessions", "By Sessions"),
            ("earnings", "By Earnings"),
            ("overall", "Overall Ranking"),
        ],
        default="overall",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)
    category = serializers.ChoiceField(choices=MentorService.SERVICE_TYPE_CHOICES, required=False)
    industry = serializers.CharField(required=False, allow_blank=True)
