from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta, datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
import stripe

from .models import (
    MentorProfile, MentorService, MentorAvailability, MentorSession,
    MentorReview, MentorApplication, MentorPayment, MentorNotification
)
from .serializers import (
    MentorProfileSerializer, MentorProfileDetailSerializer, MentorDetailSerializer, MentorServiceSerializer,
    MentorAvailabilitySerializer, MentorSessionSerializer, MentorSessionCreateSerializer,
    MentorReviewSerializer, MentorApplicationSerializer, MentorPaymentSerializer,
    MentorNotificationSerializer, MentorSearchSerializer, MentorRecommendationSerializer,
    MentorAnalyticsSerializer, MentorAvailabilitySlotSerializer, MentorRankingSerializer
)
from .services import MentorRecommendationService, MentorSearchService, MentorAnalyticsService

class MentorListView(generics.ListAPIView):
    """List all approved mentors with filtering and search"""
    serializer_class = MentorProfileSerializer
    permission_classes = []  # Allow public access to view mentors
    
    def get_queryset(self):
        queryset = MentorProfile.objects.filter(status='approved')
        
        # Apply filters
        service_type = self.request.query_params.get('service_type')
        industry = self.request.query_params.get('industry')
        min_rating = self.request.query_params.get('min_rating')
        is_verified = self.request.query_params.get('is_verified')
        
        if service_type:
            queryset = queryset.filter(services__service_type=service_type)
        
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))
        
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        return queryset.distinct().order_by('-average_rating', '-total_sessions')

    @swagger_auto_schema(
        operation_description="List all approved mentors with filtering options",
        manual_parameters=[
            openapi.Parameter('service_type', openapi.IN_QUERY, description="Filter by service type", type=openapi.TYPE_STRING),
            openapi.Parameter('industry', openapi.IN_QUERY, description="Filter by industry", type=openapi.TYPE_STRING),
            openapi.Parameter('min_rating', openapi.IN_QUERY, description="Minimum rating filter", type=openapi.TYPE_NUMBER),
            openapi.Parameter('is_verified', openapi.IN_QUERY, description="Filter by verification status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: MentorProfileSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class MentorDetailView(generics.RetrieveAPIView):
    """Get detailed mentor profile"""
    serializer_class = MentorDetailSerializer
    permission_classes = []  # Allow public access to view mentor details
    queryset = MentorProfile.objects.filter(status='approved')

    @swagger_auto_schema(
        operation_description="Get detailed mentor profile information",
        responses={200: MentorDetailSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class MentorSearchView(APIView):
    """Advanced mentor search"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Advanced mentor search with multiple filters",
        request_body=MentorSearchSerializer,
        responses={200: MentorProfileSerializer(many=True)}
    )
    def post(self, request):
        serializer = MentorSearchSerializer(data=request.data)
        if serializer.is_valid():
            mentors = MentorSearchService.search_mentors(**serializer.validated_data)
            mentor_serializer = MentorProfileSerializer(mentors, many=True)
            return Response(mentor_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MentorRecommendationView(APIView):
    """Get personalized mentor recommendations"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get personalized mentor recommendations for the user",
        request_body=MentorRecommendationSerializer,
        responses={200: openapi.Response("List of recommended mentors")}
    )
    def post(self, request):
        serializer = MentorRecommendationSerializer(data=request.data)
        if serializer.is_valid():
            recommendations = MentorRecommendationService.get_recommended_mentors(
                user=request.user,
                **serializer.validated_data
            )
            return Response(recommendations)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MentorRankingView(APIView):
    """Get mentor rankings"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get mentor rankings by different criteria",
        request_body=MentorRankingSerializer,
        responses={200: openapi.Response("List of ranked mentors")}
    )
    def post(self, request):
        serializer = MentorRankingSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            ranking_type = data.get('ranking_type', 'overall')
            
            if ranking_type == 'rating':
                mentors = MentorRecommendationService.get_mentors_by_rating(
                    limit=data.get('limit', 10)
                )
            elif ranking_type == 'sessions':
                mentors = MentorRecommendationService.get_mentors_by_sessions(
                    limit=data.get('limit', 10)
                )
            elif ranking_type == 'earnings':
                mentors = MentorRecommendationService.get_mentors_by_earnings(
                    limit=data.get('limit', 10)
                )
            else:  # overall
                mentors = MentorRecommendationService.get_top_mentors(
                    limit=data.get('limit', 10),
                    category=data.get('category'),
                    industry=data.get('industry')
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
            return Response({'error': 'Stripe not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        profile = getattr(request.user, 'mentor_profile', None)
        if not profile:
            return Response({'error': 'Not a mentor'}, status=status.HTTP_403_FORBIDDEN)

        if profile.stripe_account_id:
            return Response({'account_id': profile.stripe_account_id}, status=status.HTTP_200_OK)

        acct = stripe.Account.create(type='standard')
        profile.stripe_account_id = acct['id']
        profile.save()
        return Response({'account_id': acct['id']}, status=status.HTTP_200_OK)

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
            return Response({'error': 'Stripe not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        profile = getattr(request.user, 'mentor_profile', None)
        if not profile or not profile.stripe_account_id:
            return Response({'error': 'Stripe account not found. Create account first.'}, status=status.HTTP_400_BAD_REQUEST)

        return_url = request.query_params.get('return_url') or request.build_absolute_uri('/')
        refresh_url = request.query_params.get('refresh_url') or request.build_absolute_uri('/settings')

        link = stripe.AccountLink.create(
            account=profile.stripe_account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type='account_onboarding'
        )
        return Response({'url': link['url']}, status=status.HTTP_200_OK)

class StripeConnectStatusView(APIView):
    """Return current mentor's Stripe Connect/KYC status"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'mentor_profile', None)
        if not profile:
            return Response({'error': 'Not a mentor'}, status=status.HTTP_403_FORBIDDEN)
        return Response({
            'stripe_account_id': profile.stripe_account_id,
            'payouts_enabled': profile.payouts_enabled,
            'charges_enabled': profile.charges_enabled,
            'kyc_disabled_reason': profile.kyc_disabled_reason,
            'kyc_due_by': profile.kyc_due_by.isoformat() if profile.kyc_due_by else null,
            'capabilities': profile.stripe_capabilities,
        })

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
        
        # Get service duration if service_id is provided
        duration_minutes = 60  # default 1 hour
        if service_id:
            try:
                service = MentorService.objects.get(id=service_id, mentor=mentor, is_active=True)
                duration_minutes = service.duration_minutes
            except MentorService.DoesNotExist:
                pass
        
        day_of_week = check_date.weekday()
        availabilities = MentorAvailability.objects.filter(
            mentor=mentor,
            day_of_week=day_of_week,
            is_active=True
        )
        
        slots = []
        for availability in availabilities:
            # Generate slots based on service duration
            current_time = availability.start_time
            while current_time < availability.end_time:
                # Calculate end time for this slot
                slot_end = (datetime.combine(check_date, current_time) + timedelta(minutes=duration_minutes)).time()
                
                # Check if the entire slot fits within availability
                if slot_end <= availability.end_time:
                    # Check if this time slot is available (no conflicting sessions)
                    is_available = not MentorSession.objects.filter(
                        mentor=mentor,
                        scheduled_date=check_date,
                        scheduled_time=current_time,
                        status__in=['confirmed', 'pending']
                    ).exists()
                    
                    if is_available:
                        slots.append({
                            'date': check_date,
                            'start_time': current_time,
                            'end_time': slot_end,
                            'is_available': is_available,
                            'duration_minutes': duration_minutes
                        })
                
                # Move to next slot (30-minute intervals for selection)
                current_time = (datetime.combine(check_date, current_time) + timedelta(minutes=30)).time()
        
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
    """Get platform-wide analytics (admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
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

class MentorProfileUpdateView(generics.UpdateAPIView):
    """Update mentor profile (for mentors only)"""
    serializer_class = MentorProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'mentor_profile'):
            raise PermissionError("You must be a mentor to update profile")
        return user.mentor_profile
    
    def get_queryset(self):
        return MentorProfile.objects.filter(user=self.request.user)

class MentorServiceUpdateView(generics.UpdateAPIView):
    """Update mentor service (for mentors only)"""
    serializer_class = MentorServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'mentor_profile'):
            return MentorService.objects.none()
        return MentorService.objects.filter(mentor=user.mentor_profile)

class MentorAvailabilityUpdateView(generics.UpdateAPIView):
    """Update mentor availability (for mentors only)"""
    serializer_class = MentorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'mentor_profile'):
            return MentorAvailability.objects.none()
        return MentorAvailability.objects.filter(mentor=user.mentor_profile)
