from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.conf import settings
from zoneinfo import ZoneInfo
from datetime import date, timedelta, datetime

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings

import stripe

from .services.legacy import apply_track_ranking
from adminpanel.permissions import IsAdminUser, user_has_role

from .models import (
    MentorProfile, MentorService, MentorAvailability, MentorSession,
    MentorReview, MentorApplication, MentorPayment, MentorNotification,
    HumanReviewTask
)

from .serializers import (
    MentorProfileSerializer, MentorProfileDetailSerializer, MentorProfileCreateSerializer,
    MentorServiceSerializer, MentorAvailabilitySerializer,
    MentorSessionSerializer, MentorSessionCreateSerializer,
    MentorReviewSerializer, MentorApplicationSerializer,
    MentorPaymentSerializer, MentorNotificationSerializer,
    MentorSearchSerializer, MentorRecommendationSerializer,
    MentorAnalyticsSerializer, MentorAvailabilitySlotSerializer,
    MentorRankingSerializer, HumanReviewTaskSerializer
)

from .services.legacy import (
    MentorRecommendationService,
    MentorSearchService,
    MentorAnalyticsService
)

# ======================================================
# Pagination (GLOBAL RULE)
# ======================================================

class MentorListPagination(PageNumberPagination):
    """
    Default mentor list pagination.
    SaaS rule: Explore mentors = 6 per page.
    """
    page_size = 6
    page_size_query_param = "limit"
    max_page_size = 12


# ======================================================
# Mentor List
# ======================================================

class MentorListView(generics.ListAPIView):
    """
    List all approved mentors with filtering, ranking, and pagination.
    """
    serializer_class = MentorProfileSerializer
    permission_classes = []
    pagination_class = MentorListPagination

    def get_queryset(self):
        queryset = MentorProfile.objects.filter(
            status="approved"
        ).annotate(
            avg_rating_calc=Avg("reviews__rating"),
            review_count_calc=Count("reviews"),
        )

        # ----------------------
        # Filters
        # ----------------------
        service_type = self.request.query_params.get("service_type")
        industry = self.request.query_params.get("industry")
        min_rating = self.request.query_params.get("min_rating")
        is_verified = self.request.query_params.get("is_verified")
        track = self.request.query_params.get("track")

        if service_type:
            queryset = queryset.filter(services__service_type=service_type)

        if industry:
            queryset = queryset.filter(industry__icontains=industry)

        if min_rating:
            queryset = queryset.filter(avg_rating_calc__gte=float(min_rating))

        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == "true")

        queryset = queryset.distinct()

        # ----------------------
        # Ranking
        # ----------------------
        if track:
            queryset = queryset.filter(primary_track=track)
            queryset = apply_track_ranking(queryset, track)
        else:
            queryset = queryset.order_by(
                "-is_verified",
                "-avg_rating_calc",
                "-total_sessions",
            )

        return queryset

    @swagger_auto_schema(
        operation_description="List approved mentors with filters and pagination",
        manual_parameters=[
            openapi.Parameter("service_type", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("industry", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("min_rating", openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter("is_verified", openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter("track", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("limit", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        responses={200: MentorProfileSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ======================================================
# Mentor Detail
# ======================================================

class MentorDetailView(generics.RetrieveAPIView):
    serializer_class = MentorProfileDetailSerializer
    permission_classes = []
    queryset = MentorProfile.objects.filter(status="approved")

    @swagger_auto_schema(
        operation_description="Get detailed mentor profile",
        responses={200: MentorProfileDetailSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ======================================================
# Mentor Search
# ======================================================

class MentorSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Advanced mentor search",
        request_body=MentorSearchSerializer,
        responses={200: MentorProfileSerializer(many=True)},
    )
    def post(self, request):
        serializer = MentorSearchSerializer(data=request.data)
        if serializer.is_valid():
            mentors = MentorSearchService.search_mentors(
                **serializer.validated_data
            )
            return Response(
                MentorProfileSerializer(mentors, many=True).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# Mentor Recommendation
# ======================================================

class MentorRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get personalized mentor recommendations",
        request_body=MentorRecommendationSerializer,
        responses={200: openapi.Response("Recommended mentors")},
    )
    def post(self, request):
        serializer = MentorRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            data = MentorRecommendationService.get_recommended_mentors(
                user=request.user,
                **serializer.validated_data
            )
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# Mentor Ranking
# ======================================================

class MentorRankingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get mentor rankings",
        request_body=MentorRankingSerializer,
        responses={200: openapi.Response("Ranked mentors")},
    )
    def post(self, request):
        serializer = MentorRankingSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            ranking_type = data.get("ranking_type", "overall")

            if ranking_type == "rating":
                mentors = MentorRecommendationService.get_mentors_by_rating(
                    limit=data.get("limit", 10)
                )
            elif ranking_type == "sessions":
                mentors = MentorRecommendationService.get_mentors_by_sessions(
                    limit=data.get("limit", 10)
                )
            elif ranking_type == "earnings":
                mentors = MentorRecommendationService.get_mentors_by_earnings(
                    limit=data.get("limit", 10)
                )
            else:
                mentors = MentorRecommendationService.get_top_mentors(
                    limit=data.get("limit", 10),
                    category=data.get("category"),
                    industry=data.get("industry"),
                )

            return Response(mentors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      

class StripeConnectCreateAccountView(APIView):
    """Create or fetch Stripe Connect account for the authenticated mentor"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create Stripe Connect account for current mentor and return account_id",
        responses={200: openapi.Response(description="Account created", examples={"application/json": {"account_id": "acct_..."}})}
    )
    def post(self, request):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            return Response({'error': 'Stripe not configured', 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

        profile = getattr(request.user, 'mentor_profile', None)
        if not profile:
            return Response({'error': 'Not a mentor'}, status=status.HTTP_403_FORBIDDEN)

        if profile.stripe_account_id:
            return Response({'account_id': profile.stripe_account_id}, status=status.HTTP_200_OK)

        try:
            acct = stripe.Account.create(type='standard')
            profile.stripe_account_id = acct['id']
            profile.save()
            return Response({'account_id': acct['id']}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e), 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

class StripeConnectCreateAccountLinkView(APIView):
    """Create an onboarding account link for the mentor's Stripe account"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create Stripe Connect account onboarding link",
        manual_parameters=[
            openapi.Parameter('return_url', openapi.IN_QUERY, description='Return URL after onboarding', type=openapi.TYPE_STRING),
            openapi.Parameter('refresh_url', openapi.IN_QUERY, description='Refresh URL if onboarding is interrupted', type=openapi.TYPE_STRING),
        ],
        responses={200: openapi.Response(description="Link created", examples={"application/json": {"url": "https://connect.stripe.com/..."}})}
    )
    def post(self, request):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            return Response({'error': 'Stripe not configured', 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

        profile = getattr(request.user, 'mentor_profile', None)
        if not profile or not profile.stripe_account_id:
            return Response({'error': 'Stripe account not found. Create account first.'}, status=status.HTTP_400_BAD_REQUEST)

        return_url = request.query_params.get('return_url') or request.build_absolute_uri('/')
        refresh_url = request.query_params.get('refresh_url') or request.build_absolute_uri('/settings')

        try:
            link = stripe.AccountLink.create(
                account=profile.stripe_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding'
            )
            return Response({'url': link['url']}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e), 'service': 'stripe'}, status=status.HTTP_502_BAD_GATEWAY)

class StripeConnectStatusView(APIView):
    """
    READ-ONLY endpoint for Stripe Connect status.
    
    Safe for automatic frontend probing.
    Returns connection status without mutations.
    
    GateAI OS Contract:
    - This endpoint performs NO mutations
    - This endpoint is safe for GET requests
    - This endpoint can be auto-probed on page load
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get Stripe Connect status for the current user"""
        profile = getattr(request.user, 'mentor_profile', None)
        
        # User has no mentor profile - return safe defaults
        if not profile:
            return Response({
                'is_connected': False,
                'requires_action': True,
                'can_set_availability': False,
                'payouts_enabled': False,
                'charges_enabled': False,
                'has_account': False,
            }, status=status.HTTP_200_OK)
        
        # User has mentor profile - return connection status
        has_account = bool(profile.stripe_account_id)
        is_connected = has_account and profile.payouts_enabled and profile.charges_enabled
        
        return Response({
            'is_connected': is_connected,
            'requires_action': not is_connected,
            'can_set_availability': is_connected,
            'payouts_enabled': profile.payouts_enabled,
            'charges_enabled': profile.charges_enabled,
            'has_account': has_account,
            'stripe_account_id': profile.stripe_account_id if has_account else None,
            'kyc_disabled_reason': profile.kyc_disabled_reason if not is_connected else None,
            'kyc_due_by': profile.kyc_due_by.isoformat() if profile.kyc_due_by else None,
        }, status=status.HTTP_200_OK)

class MentorServiceView(generics.ListCreateAPIView):
    """List and create mentor services"""
    serializer_class = MentorServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        mentor_id = self.kwargs.get('mentor_id')
        return MentorService.objects.filter(mentor_id=mentor_id, is_active=True)
    
    def perform_create(self, serializer):
        mentor = get_object_or_404(MentorProfile, id=self.kwargs.get('mentor_id'))
        serializer.save(mentor=mentor)

class MentorAvailabilityView(generics.ListCreateAPIView):
    """List and create mentor availability"""
    serializer_class = MentorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        mentor_id = self.kwargs.get('mentor_id')
        return MentorAvailability.objects.filter(mentor_id=mentor_id, is_active=True)
    
    def perform_create(self, serializer):
        mentor = get_object_or_404(MentorProfile, id=self.kwargs.get('mentor_id'))
        serializer.save(mentor=mentor)

class MentorAvailabilitySlotsView(APIView):
    """Get available time slots for a mentor"""
    permission_classes = []  # Allow public access to view availability
    
    @swagger_auto_schema(
        operation_description="Get available time slots for a mentor on a specific date",
        manual_parameters=[
            openapi.Parameter('date', openapi.IN_QUERY, description="Date to check availability", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('service_id', openapi.IN_QUERY, description="Service ID to get duration", type=openapi.TYPE_INTEGER),
        ],
        responses={200: MentorAvailabilitySlotSerializer(many=True)}
    )
    def get(self, request, mentor_id):
        mentor = get_object_or_404(MentorProfile, id=mentor_id, status='approved')
        check_date = request.query_params.get('date', date.today())
        service_id = request.query_params.get('service_id')
        
        if isinstance(check_date, str):
            check_date = date.fromisoformat(check_date)
        
        # Use fixed 1-hour slots for availability
        slot_minutes = 60
        
        mentor_tz_value = getattr(mentor, "timezone", settings.TIME_ZONE) or settings.TIME_ZONE
        try:
            mentor_tz = ZoneInfo(mentor_tz_value)
        except Exception:
            mentor_tz = ZoneInfo(settings.TIME_ZONE)

        day_of_week = check_date.weekday()
        availabilities = MentorAvailability.objects.filter(
            mentor=mentor,
            day_of_week=day_of_week,
            is_active=True
        )
        
        slots = []
        for availability in availabilities:
            # Generate slots based on fixed slot size (default 1 hour)
            current_time = availability.start_time
            while current_time < availability.end_time:
                # Calculate end time for this slot
                slot_end = (datetime.combine(check_date, current_time) + timedelta(minutes=slot_minutes)).time()
                
                # Check if the entire slot fits within availability
                if slot_end <= availability.end_time:
                    # Check if this time slot is available (no conflicting sessions)
                    slot_datetime_start = timezone.make_aware(
                        datetime.combine(check_date, current_time),
                        timezone=mentor_tz
                    )
                    slot_datetime_end = timezone.make_aware(
                        datetime.combine(check_date, slot_end),
                        timezone=mentor_tz
                    )
                    slot_start_utc = slot_datetime_start.astimezone(timezone.utc)
                    slot_end_utc = slot_datetime_end.astimezone(timezone.utc)
                    
                    has_conflicting_session = MentorSession.objects.filter(
                        mentor=mentor,
                        scheduled_date=check_date,
                        scheduled_time=current_time,
                        status__in=['confirmed', 'pending']
                    ).exists()
                    
                    # Check TimeSlot holds from decision_slots app
                    from appointments.models import Appointment, TimeSlot
                    now = timezone.now()
                    conflicting_timeslot = TimeSlot.objects.filter(
                        mentor=mentor,
                        start_time__lt=slot_end_utc,
                        end_time__gt=slot_start_utc,
                        is_available=False
                    ).filter(
                        Q(reserved_until__isnull=False) &
                        Q(reserved_until__gte=now) &
                        Q(reserved_appointment__status='pending')
                    ).exists()
                    
                    # Release expired holds (lightweight check)
                    expired_holds = TimeSlot.objects.filter(
                        mentor=mentor,
                        start_time__lt=slot_end_utc,
                        end_time__gt=slot_start_utc,
                        is_available=False,
                        reserved_until__lt=now,
                        reserved_appointment__status='pending'
                    )
                    for expired_slot in expired_holds:
                        expired_slot.is_available = True
                        expired_slot.reserved_until = None
                        if expired_slot.reserved_appointment:
                            expired_slot.reserved_appointment.status = 'expired'
                            expired_slot.reserved_appointment.save()
                        expired_slot.reserved_appointment = None
                        expired_slot.save()
                    
                    is_available = not has_conflicting_session and not conflicting_timeslot
                    
                    # Find or create matching TimeSlot
                    matching_timeslot = TimeSlot.objects.filter(
                        mentor=mentor,
                        start_time=slot_start_utc,
                        end_time=slot_end_utc
                    ).first()
                    
                    if not matching_timeslot:
                        # Create TimeSlot on the fly for booking
                        from decimal import Decimal
                        service_price = Decimal('0.00')
                        if service_id:
                            try:
                                service = MentorService.objects.get(id=service_id, mentor=mentor, is_active=True)
                                if hasattr(service, 'fixed_price') and service.fixed_price:
                                    service_price = Decimal(str(service.fixed_price))
                                elif hasattr(service, 'price_per_hour') and service.price_per_hour:
                                    service_price = Decimal(str(service.price_per_hour)) * Decimal(str(duration_minutes)) / Decimal('60')
                            except MentorService.DoesNotExist:
                                pass
                        
                        matching_timeslot = TimeSlot.objects.create(
                            mentor=mentor,
                            start_time=slot_start_utc,
                            end_time=slot_end_utc,
                            is_available=True,
                            price=service_price,
                            currency='USD'
                        )
                    
                    slot_id = matching_timeslot.id
                    
                    if is_available:
                        slots.append({
                            'date': check_date,
                            'start_time': current_time,
                            'end_time': slot_end,
                            'is_available': is_available,
                            'duration_minutes': slot_minutes,
                            'slot_id': slot_id
                        })
                
                # Move to next slot (fixed slot size)
                current_time = (datetime.combine(check_date, current_time) + timedelta(minutes=slot_minutes)).time()
        
        serializer = MentorAvailabilitySlotSerializer(slots, many=True)
        return Response(serializer.data)

class MentorSessionView(generics.ListCreateAPIView):
    """List and create mentor sessions"""
    serializer_class = MentorSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            # Mentor viewing their sessions
            return MentorSession.objects.filter(mentor=user.mentor_profile)
        else:
            # User viewing their booked sessions
            return MentorSession.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MentorSessionCreateSerializer
        return MentorSessionSerializer

class MentorSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detail view for mentor sessions"""
    serializer_class = MentorSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorSession.objects.none()
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorSession.objects.filter(mentor=user.mentor_profile)
        else:
            return MentorSession.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark session as completed"""
        session = self.get_object()
        session.complete_session()
        return Response({'status': 'Session completed'})

class MentorReviewView(generics.ListCreateAPIView):
    """List and create mentor reviews"""
    serializer_class = MentorReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorReview.objects.none()
        mentor_id = self.kwargs.get('mentor_id')
        return MentorReview.objects.filter(mentor_id=mentor_id)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if getattr(self, 'swagger_fake_view', False):
            return context
        mentor_id = self.kwargs.get('mentor_id')
        context['mentor'] = get_object_or_404(MentorProfile, id=mentor_id)
        return context

class MentorApplicationView(generics.CreateAPIView):
    """Create mentor application"""
    serializer_class = MentorApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class MentorApplicationStatusView(generics.RetrieveAPIView):
    """Check application status"""
    serializer_class = MentorApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorApplication()
        return get_object_or_404(MentorApplication, user=self.request.user)

class MentorPaymentView(generics.ListAPIView):
    """List mentor payments"""
    serializer_class = MentorPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorPayment.objects.none()
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorPayment.objects.filter(mentor=user.mentor_profile)
        else:
            return MentorPayment.objects.filter(session__user=user)

class MentorNotificationView(generics.ListAPIView):
    """List mentor notifications"""
    serializer_class = MentorNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorNotification.objects.none()
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorNotification.objects.filter(mentor=user.mentor_profile)
        else:
            return MentorNotification.objects.none()  # Users don't have notifications yet

class MentorNotificationDetailView(generics.RetrieveUpdateAPIView):
    """Detail view for notifications"""
    serializer_class = MentorNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MentorNotification.objects.none()
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorNotification.objects.filter(mentor=user.mentor_profile)
        else:
            return MentorNotification.objects.none()
    
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        if request.data.get('mark_as_read'):
            notification.mark_as_read()
        return Response({'status': 'Notification updated'})

class MentorAnalyticsView(APIView):
    """Get mentor analytics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get analytics for a mentor",
        request_body=MentorAnalyticsSerializer,
        responses={200: openapi.Response("Mentor analytics data")}
    )
    def post(self, request, mentor_id):
        mentor = get_object_or_404(MentorProfile, id=mentor_id)
        serializer = MentorAnalyticsSerializer(data=request.data)
        
        if serializer.is_valid():
            analytics = MentorAnalyticsService.get_mentor_analytics(
                mentor=mentor,
                days=serializer.validated_data.get('days', 30)
            )
            return Response(analytics)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlatformAnalyticsView(APIView):
    """Platform-wide analytics (admin only)"""
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get platform-wide analytics (admin only)",
        request_body=MentorAnalyticsSerializer,
        responses={200: openapi.Response("Platform analytics data")}
    )
    def post(self, request):
        serializer = MentorAnalyticsSerializer(data=request.data)
        
        if serializer.is_valid():
            analytics = MentorAnalyticsService.get_platform_analytics(
                days=serializer.validated_data.get('days', 30)
            )
            return Response(analytics)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MentorProfileStatusView(APIView):
    """
    READ-ONLY endpoint to get mentor profile status for the authenticated user.
    
    This endpoint is safe for automatic frontend probing/prefetching.
    
    Returns:
    - 200 with profile status if user has a mentor profile
    - 200 with has_profile=false if user has no mentor profile
    
    GateAI OS Contract:
    - This endpoint performs NO mutations
    - This endpoint is safe for GET requests
    - This endpoint can be auto-probed on page load
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get mentor profile status for the current user"""
        user = request.user
        
        # Check if user has a mentor profile
        if not hasattr(user, 'mentor_profile'):
            return Response({
                'has_profile': False,
                'mentor_profile_id': None,
                'application_status': None,
                'can_update_profile': False
            }, status=status.HTTP_200_OK)
        
        # User has a mentor profile
        mentor_profile = user.mentor_profile
        
        return Response({
            'has_profile': True,
            'mentor_profile_id': mentor_profile.id,
            'application_status': mentor_profile.status,
            'can_update_profile': True
        }, status=status.HTTP_200_OK)


class MentorProfileCreateView(generics.CreateAPIView):
    """
    CREATE mentor profile for authenticated user.
    
    This endpoint is for CREATING a new mentor profile.
    Use PATCH /profile/update/ for updating an existing profile.
    
    System defaults are set automatically:
    - status = "draft"
    - timezone = user.timezone OR settings.TIME_ZONE OR "UTC"
    - starting_price = Decimal("0.00")
    - average_rating = Decimal("0.00")
    - total_reviews = 0
    - total_earnings = Decimal("0.00")
    - total_sessions = 0
    - is_verified = False
    - payouts_enabled = False
    - charges_enabled = False
    - specializations = []
    
    Returns 201 Created with mentor_profile_id on success.
    Returns 400 if profile already exists or validation fails.
    """
    serializer_class = MentorProfileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Check if profile already exists
        if hasattr(user, 'mentor_profile'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': 'Mentor profile already exists. Use PATCH /profile/update/ to update it.'
            })
        
        # Create the profile with user
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        """Override to return mentor_profile_id in response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return created profile data with explicit mentor_profile_id
        profile = serializer.instance
        response_data = {
            'id': profile.id,
            'mentor_profile_id': profile.id,
            'status': profile.status,
            'message': 'Mentor profile created successfully',
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class MentorProfileUpdateView(generics.RetrieveUpdateAPIView):
    """Get and update mentor profile (for mentors only)"""
    serializer_class = MentorProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'mentor_profile'):
            raise PermissionDenied("You must be a mentor to update profile")
        return user.mentor_profile
    
    def get_queryset(self):
        return MentorProfile.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Handle PATCH requests with validation for primary_service_id"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        from django.contrib.auth import get_user_model
        from signal_delivery.services.dispatcher import notify
        from signal_delivery.services.rules import NotificationType

        User = get_user_model()
        admin_users = User.objects.filter(role="admin")
        for admin_user in admin_users:
            notify(
                NotificationType.ADMIN_MENTOR_PROFILE_UPDATED,
                context={
                    'mentor_id': instance.id,
                    'admin': admin_user,
                },
                title='Mentor profile updated',
                message=(
                    f'Mentor {instance.user.get_full_name() or instance.user.username} '
                    'updated their profile and needs review.'
                ),
                priority='normal',
                related_mentor=instance,
                payload={'mentor_id': instance.id},
            )
        return Response(serializer.data)

class MentorServiceUpdateView(generics.UpdateAPIView):
    """Update mentor service (for mentors only)"""
    serializer_class = MentorServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Allow superadmin to access any mentor service
        if user_has_role(user, 'superadmin'):
            return MentorService.objects.all()
        if not hasattr(user, 'mentor_profile'):
            return MentorService.objects.none()
        return MentorService.objects.filter(mentor=user.mentor_profile)

class MentorAvailabilityUpdateView(generics.UpdateAPIView):
    """Update mentor availability (for mentors only)"""
    serializer_class = MentorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Allow superadmin to access any mentor availability
        if user_has_role(user, 'superadmin'):
            return MentorAvailability.objects.all()
        if not hasattr(user, 'mentor_profile'):
            return MentorAvailability.objects.none()
        return MentorAvailability.objects.filter(mentor=user.mentor_profile)


class HumanReviewTaskListView(generics.ListAPIView):
    """
    List Human Review Tasks for a DecisionSlot.
    
    GET /api/v1/human-loop/review-tasks/?decision_slot_id=<id>
    
    Object-level permissions: Users can only access tasks for decision slots they own.
    Staff/admin can access all tasks.
    """
    serializer_class = HumanReviewTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from .permissions import filter_review_tasks_by_ownership, user_can_access_decision_slot
        
        decision_slot_id = self.request.query_params.get('decision_slot_id')
        
        # Apply object-level permissions: filter to user's allowed decision slots
        queryset = filter_review_tasks_by_ownership(HumanReviewTask.objects.all(), self.request.user)
        
        # If specific decision_slot_id requested, check access and filter
        if decision_slot_id:
            # Check if user can access this decision slot
            if not user_can_access_decision_slot(self.request.user, decision_slot_id):
                # Return 404 to avoid leaking existence
                from django.http import Http404
                raise Http404("Decision slot not found or access denied")
            
            queryset = queryset.filter(decision_slot_id=decision_slot_id)
        
        # Optional: filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Optional: filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Return review tasks with summary"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'decision_slot_id': request.query_params.get('decision_slot_id'),
            'review_tasks': serializer.data,
            'total_count': len(serializer.data),
            'pending_count': len([t for t in serializer.data if t.get('status') == 'pending']),
            'completed_count': len([t for t in serializer.data if t.get('status') == 'completed']),
        })


class HumanReviewTaskDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single Human Review Task.
    
    GET /api/v1/human-loop/review-tasks/<id>/
    
    Object-level permissions: Users can only access tasks for decision slots they own.
    Staff/admin can access all tasks.
    """
    serializer_class = HumanReviewTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from .permissions import filter_review_tasks_by_ownership
        
        # Apply object-level permissions: filter to user's allowed decision slots
        return filter_review_tasks_by_ownership(HumanReviewTask.objects.all(), self.request.user)
