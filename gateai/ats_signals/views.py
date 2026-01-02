from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.exceptions import PermissionDenied
import logging
from rest_framework.throttling import UserRateThrottle
from rest_framework.settings import api_settings
from django.http import FileResponse

from .models import (
    Resume, ResumeAnalysis, ResumeFeedback, ResumeComparison,
    ResumeTemplate, ResumeExport, JobDescription, ResumeJobMatch,
    KeywordMatch, UserSubscription, InvitationCode,
    UserDataConsent, LegalDisclaimer, UserDisclaimerConsent,
    ATSSignal
)
from .serializers import (
    ResumeSerializer, ResumeCreateSerializer, ResumeAnalysisSerializer,
    ResumeAnalysisRequestSerializer, ResumeFeedbackSerializer,
    ResumeComparisonSerializer, ResumeComparisonCreateSerializer,
    ResumeTemplateSerializer, ResumeExportSerializer, ResumeExportCreateSerializer,
    ResumeSearchSerializer, ResumeFilterSerializer, ResumeStatsSerializer,
    ResumeAnalysisResultSerializer, JobDescriptionSerializer, ResumeJobMatchSerializer,
    KeywordMatchSerializer, UserSubscriptionSerializer,
    InvitationCodeSerializer,
    ExternalJobCrawlRequestSerializer, ExternalResumeMatchRequestSerializer,
    UserDataConsentSerializer, LegalDisclaimerSerializer,
    UserDisclaimerConsentSerializer, DataDeletionRequestSerializer
)
# All legacy services removed - use OS-native services or direct model queries
# Legacy service removals:
# - ResumeComparisonService: removed (stubbed in ResumeComparisonView)
# - ResumeStatsService: removed (stubbed in ResumeStatsView)
# - ResumeCacheService: removed (not used in views)
# - ResumeSearchService: removed (replaced with direct Resume model queries)
# - ResumeAnalysisService: removed (use ResumeAuditEngine via /api/engines/signal-core/resume-audit/)
# JDManager functionality moved to external service
from .tier_service import TierFactory, TierService
from .data_management import DataConsentManager, LegalComplianceManager
from .referral_service import ReferralService, PricingService
from .external_services import ExternalServiceManager
from .models import ExternalServiceIntegration
import requests
from .models import DataDeletionRequest, DataExportJob
import secrets
from signal_delivery.services.dispatcher import notify
from signal_delivery.services.rules import NotificationType
from gateai.external_services.utils import ExternalServiceError, RateLimitError, AuthenticationError
from .services.persistence import filter_signals_by_ownership, user_can_access_decision_slot

# OS Engine imports - legacy compatibility
from .services.legacy_compat import analyze_resume_legacy

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _require_student(request) -> None:
    if getattr(request.user, 'role', None) != 'student':
        raise PermissionDenied("Student role required")


class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'


class AIAnalysisRateThrottle(UserRateThrottle):
    scope = 'ai_analysis'
    rate = '10/day'

    def get_rate(self):
        rates = getattr(api_settings, 'DEFAULT_THROTTLE_RATES', {}) or {}
        return rates.get(self.scope, self.rate)

class ResumeListView(generics.ListCreateAPIView):
    """Resume List and Create View with tier support"""
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check upload limit
        tier_service = TierService(self.request.user)
        if not tier_service.can_upload_resume():
            raise PermissionDenied("Monthly upload limit reached. Upgrade to Premium for unlimited uploads.")
        
        # Create resume
        resume = serializer.save(user=self.request.user)
        notify(
            NotificationType.RESUME_UPLOADED,
            context={
                "resume_id": resume.id,
                "student": self.request.user,
            },
            title="Resume uploaded",
            message="Your resume has been uploaded successfully.",
            priority="normal",
            related_resume=resume,
        )
        
        # Increment usage
        tier_service.increment_upload_count()
        
        return resume
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResumeCreateSerializer
        return ResumeSerializer
    
    @swagger_auto_schema(
        operation_description="List all resumes for the authenticated user",
        responses={200: ResumeSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Upload a new resume",
        request_body=ResumeCreateSerializer,
        responses={201: ResumeSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a resume"""
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Resume.objects.none()
        return Resume.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Get detailed information about a resume",
        responses={200: ResumeSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update resume information",
        request_body=ResumeSerializer,
        responses={200: ResumeSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a resume",
        responses={204: "No content"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class ResumeDownloadView(generics.GenericAPIView):
    """Download a resume file"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        resume = get_object_or_404(Resume, id=kwargs.get('pk'), user=request.user)
        if not resume.file:
            return Response({'error': 'Resume file not found'}, status=status.HTTP_404_NOT_FOUND)
        filename = resume.file.name.split('/')[-1]
        return FileResponse(resume.file.open('rb'), as_attachment=True, filename=filename)

class ResumeAnalysisView(generics.CreateAPIView):
    """Analyze a resume using AI"""
    serializer_class = ResumeAnalysisRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIAnalysisRateThrottle]
    
    @swagger_auto_schema(
        operation_description="Analyze a resume using AI",
        request_body=ResumeAnalysisRequestSerializer,
        responses={
            200: ResumeAnalysisResultSerializer,
            400: "Bad request",
            404: "Resume not found"
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        resume_id = serializer.validated_data['resume_id']
        industry = serializer.validated_data.get('industry')
        job_title = serializer.validated_data.get('job_title')
        consent = serializer.validated_data.get('consent', False)
        consent_version = serializer.validated_data.get('consent_version', '1.0')
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check if resume exists and belongs to user
        resume = get_object_or_404(Resume, id=resume_id, user=request.user)
        
        # Check if already analyzed
        if resume.has_analysis:
            return Response({
                'message': 'Resume already analyzed',
                'resume': ResumeSerializer(resume).data,
                'analysis': ResumeAnalysisSerializer(resume.analysis).data,
                'feedback': ResumeFeedbackSerializer(resume.analysis.feedback).data
            }, status=status.HTTP_200_OK)

        # Check consent requirements
        required_disclaimers = LegalComplianceManager.get_required_disclaimers(request.user)
        if consent:
            DataConsentManager.grant_consent(
                request.user,
                'data_processing',
                ip_address=ip_address,
                user_agent=user_agent,
                consent_version=consent_version
            )
            for disclaimer in required_disclaimers:
                LegalComplianceManager.record_disclaimer_consent(
                    request.user,
                    disclaimer,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            required_disclaimers = []

        missing_data_consent = not DataConsentManager.has_consent(request.user, 'data_processing')
        if missing_data_consent or required_disclaimers:
            return Response(
                {
                    'error': 'Consent required before resume analysis',
                    'missing_data_processing_consent': missing_data_consent,
                    'required_disclaimers': [
                        {
                            'type': disclaimer.disclaimer_type,
                            'title': disclaimer.title,
                            'version': disclaimer.version
                        }
                        for disclaimer in required_disclaimers
                    ],
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check tier quota
        tier_service = TierService(request.user)
        if not tier_service.can_analyze_resume():
            logger.info(
                "Resume analysis blocked: quota exceeded",
                extra={"user_id": request.user.id, "resume_id": resume_id}
            )
            return Response(
                {'error': 'Monthly analysis limit reached. Upgrade to Premium for unlimited analyses.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Perform analysis via OS Engine (legacy compatibility wrapper)
            analysis = analyze_resume_legacy(resume_id, industry, job_title)
            
            # Prepare response
            result_data = {
                'resume': ResumeSerializer(resume).data,
                'analysis': ResumeAnalysisSerializer(analysis).data,
                'feedback': ResumeFeedbackSerializer(analysis.feedback).data,
                'processing_time': analysis.processing_time,
                'analysis_status': 'completed_with_fallback' if getattr(analysis, 'fallback_used', False) else 'completed'
            }

            tier_service.increment_analysis_count()
            
            return Response(result_data, status=status.HTTP_200_OK)
            
        except ExternalServiceError as e:
            status_code = status.HTTP_502_BAD_GATEWAY
            if isinstance(e, RateLimitError):
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            elif isinstance(e, AuthenticationError):
                status_code = status.HTTP_502_BAD_GATEWAY

            logger.exception(
                "Resume analysis external service failed",
                extra={"user_id": request.user.id, "resume_id": resume_id, "service": e.service}
            )
            return Response(
                {'error': e.message, 'service': e.service},
                status=status_code
            )
        except Exception as e:
            logger.exception(
                "Resume analysis failed",
                extra={"user_id": request.user.id, "resume_id": resume_id}
            )
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ResumeAnalysisDetailView(generics.RetrieveAPIView):
    """Get analysis results for a resume"""
    serializer_class = ResumeAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ResumeAnalysis.objects.none()
        return ResumeAnalysis.objects.filter(resume__user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Get analysis results for a resume",
        responses={200: ResumeAnalysisSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ResumeAnalysisByResumeView(generics.RetrieveAPIView):
    """Get analysis results by resume id"""
    serializer_class = ResumeAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        resume_id = self.kwargs.get('resume_id')
        return get_object_or_404(
            ResumeAnalysis,
            resume_id=resume_id,
            resume__user=self.request.user
        )

class ResumeFeedbackView(generics.RetrieveAPIView):
    """Get feedback for a resume analysis"""
    serializer_class = ResumeFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ResumeFeedback.objects.none()
        return ResumeFeedback.objects.filter(analysis__resume__user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Get detailed feedback for a resume analysis",
        responses={200: ResumeFeedbackSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ResumeFeedbackByResumeView(generics.RetrieveAPIView):
    """Get feedback by resume id"""
    serializer_class = ResumeFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        resume_id = self.kwargs.get('resume_id')
        return get_object_or_404(
            ResumeFeedback,
            analysis__resume_id=resume_id,
            analysis__resume__user=self.request.user
        )

class ExternalJobCrawlerView(generics.CreateAPIView):
    """Trigger external job crawling and store results"""
    serializer_class = ExternalJobCrawlRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BurstRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_title = serializer.validated_data['job_title']
        location = serializer.validated_data['location']
        sources = serializer.validated_data.get('sources')
        limit = serializer.validated_data.get('limit', 20)

        try:
            # ✅ request-time 创建（唯一正确方式）
            manager = ExternalServiceManager()

            stored = manager.crawl_and_store_jobs(
                job_title=job_title,
                location=location,
                sources=sources,
                limit=limit,
                user=request.user
            )

            return Response(
                JobDescriptionSerializer(stored, many=True).data,
                status=status.HTTP_200_OK
            )

        except ExternalServiceError as e:
            status_code = status.HTTP_502_BAD_GATEWAY
            if isinstance(e, RateLimitError):
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Response(
                {'error': e.message, 'service': e.service, 'fallback': True},
                status=status_code
            )
        except Exception:
            return Response(
                {'error': 'External service unavailable', 'fallback': True},
                status=status.HTTP_502_BAD_GATEWAY
            )

class ExternalResumeMatcherView(generics.CreateAPIView):
    """Match a resume to an existing job description via external ResumeMatcher service"""
    serializer_class = ExternalResumeMatchRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [BurstRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume = get_object_or_404(
            Resume,
            id=serializer.validated_data['resume_id'],
            user=request.user
        )
        job = get_object_or_404(
            JobDescription,
            id=serializer.validated_data['job_description_id']
        )

        try:
            # ✅ request-time 创建
            manager = ExternalServiceManager()

            match = manager.match_resume_to_external_jd(
                resume=resume,
                job_description=job,
                user=request.user
            )

            if not match:
                return Response(
                    {'error': 'Matching failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                ResumeJobMatchSerializer(match).data,
                status=status.HTTP_200_OK
            )

        except ExternalServiceError as e:
            status_code = status.HTTP_502_BAD_GATEWAY
            if isinstance(e, RateLimitError):
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Response(
                {'error': e.message, 'service': e.service, 'fallback': True},
                status=status_code
            )
        except Exception:
            return Response(
                {'error': 'External service unavailable', 'fallback': True},
                status=status.HTTP_502_BAD_GATEWAY
            )
class ExternalServicesHealthView(generics.GenericAPIView):
    """Health check for external service integrations (ResumeMatcher, JobCrawler)"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Check health/status of configured external services",
        responses={200: 'OK'}
    )
    def get(self, request, *args, **kwargs):
        try:
            # Check JobCrawler health
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            job_crawler_health = job_crawler_service.check_health()
            
            # Check ResumeMatcher health
            from gateai.external_services.third_party_apis.resume_matcher import resume_matcher_service
            resume_matcher_health = resume_matcher_service.check_health()
            
            results = {
                'job_crawler': {
                    'status': job_crawler_health.get('status', 'unknown'),
                    'error': job_crawler_health.get('error', None)
                },
                'resume_matcher': {
                    'status': resume_matcher_health.get('status', 'unknown'),
                    'error': resume_matcher_health.get('error', None)
                },
                'ai_analyzer': {
                    'status': 'not_implemented',
                    'error': 'AI Analyzer service not yet implemented'
                }
            }
            
            return Response(results, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResumeSearchView(generics.ListAPIView):
    """Search resumes with filters"""
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Search resumes with various filters",
        request_body=ResumeSearchSerializer,
        responses={200: ResumeSerializer(many=True)}
    )
    def post(self, request, *args, **kwargs):
        serializer = ResumeSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data.get('query')
        status_filter = serializer.validated_data.get('status')
        date_from = serializer.validated_data.get('date_from')
        date_to = serializer.validated_data.get('date_to')
        
        # Direct Resume model query (replaces ResumeSearchService)
        from django.db.models import Q
        resumes = Resume.objects.filter(user=request.user)
        
        if query:
            resumes = resumes.filter(
                Q(title__icontains=query) |
                Q(file__icontains=query)
            )
        
        if status_filter:
            resumes = resumes.filter(status=status_filter)
        
        if date_from:
            resumes = resumes.filter(uploaded_at__date__gte=date_from)
        
        if date_to:
            resumes = resumes.filter(uploaded_at__date__lte=date_to)
        
        resumes = resumes.order_by('-created_at')
        
        page = self.paginate_queryset(resumes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(resumes, many=True)
        return Response(serializer.data)

class ResumeFilterView(generics.ListAPIView):
    """Filter resumes"""
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Filter resumes based on various criteria",
        request_body=ResumeFilterSerializer,
        responses={200: ResumeSerializer(many=True)}
    )
    def post(self, request, *args, **kwargs):
        serializer = ResumeFilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        filters = serializer.validated_data
        
        # Direct Resume model query (replaces ResumeSearchService)
        from django.utils import timezone as tz
        resumes = Resume.objects.filter(user=request.user)
        
        if filters.get('status'):
            resumes = resumes.filter(status=filters['status'])
        
        if filters.get('file_type'):
            resumes = resumes.filter(file_type=filters['file_type'])
        
        if filters.get('has_analysis') is not None:
            if filters['has_analysis']:
                resumes = resumes.filter(analysis__isnull=False)
            else:
                resumes = resumes.filter(analysis__isnull=True)
        
        if filters.get('date_range'):
            date_range = filters['date_range']
            today = tz.now().date()
            
            if date_range == 'today':
                resumes = resumes.filter(uploaded_at__date=today)
            elif date_range == 'week':
                from datetime import timedelta
                week_ago = today - timedelta(days=7)
                resumes = resumes.filter(uploaded_at__date__gte=week_ago)
            elif date_range == 'month':
                from datetime import timedelta
                month_ago = today - timedelta(days=30)
                resumes = resumes.filter(uploaded_at__date__gte=month_ago)
            elif date_range == 'year':
                from datetime import timedelta
                year_ago = today - timedelta(days=365)
                resumes = resumes.filter(uploaded_at__date__gte=year_ago)
        
        resumes = resumes.order_by('-created_at')
        
        page = self.paginate_queryset(resumes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(resumes, many=True)
        return Response(serializer.data)

class ResumeStatsView(generics.RetrieveAPIView):
    """Get resume statistics for user"""
    serializer_class = ResumeStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        if getattr(self, 'swagger_fake_view', False):
            return None
        # ResumeStatsService removed - return basic stats from ATSSignal
        from decimal import Decimal
        from django.db.models import Avg, Count
        
        # Get basic stats from ATSSignal model
        user_signals = ATSSignal.objects.filter(
            details__user_id=str(self.request.user.id)
        )
        
        stats = {
            'total_resumes': 0,  # Legacy field - not applicable to OS architecture
            'analyzed_resumes': 0,  # Legacy field
            'pending_analysis': 0,  # Legacy field
            'average_score': Decimal('0.00'),  # Legacy field
            'score_distribution': {
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'needs_improvement': 0,
                'poor': 0,
            },
            'recent_uploads': [],  # Legacy field
            # OS-native stats
            'total_signals': user_signals.count(),
            'critical_signals': user_signals.filter(severity='critical').count(),
            'high_signals': user_signals.filter(severity='high').count(),
            'medium_signals': user_signals.filter(severity='medium').count(),
            'low_signals': user_signals.filter(severity='low').count(),
        }
        return stats
    
    @swagger_auto_schema(
        operation_description="Get resume statistics for the authenticated user",
        responses={200: ResumeStatsSerializer}
    )
    def get(self, request, *args, **kwargs):
        stats = self.get_object()
        serializer = self.get_serializer(stats)
        return Response(serializer.data)

class ResumeComparisonView(generics.ListCreateAPIView):
    """List and create resume comparisons"""
    serializer_class = ResumeComparisonSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ResumeComparison.objects.none()
        return ResumeComparison.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResumeComparisonCreateSerializer
        return ResumeComparisonSerializer
    
    @swagger_auto_schema(
        operation_description="List all resume comparisons for the user",
        responses={200: ResumeComparisonSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new resume comparison",
        request_body=ResumeComparisonCreateSerializer,
        responses={201: ResumeComparisonSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create comparison
        comparison = serializer.save(user=request.user)
        
        # ResumeComparisonService removed - service refactored
        # Stub metrics for backward compatibility
        try:
            # Basic stub metrics
            comparison.score_improvement = 0
            comparison.improvement_areas = []
            comparison.maintained_strengths = []
            comparison.save()
            
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            ResumeComparisonSerializer(comparison).data,
            status=status.HTTP_201_CREATED
        )

class ResumeTemplateListView(generics.ListAPIView):
    """List available resume templates"""
    serializer_class = ResumeTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ResumeTemplate.objects.filter(is_active=True)
    
    @swagger_auto_schema(
        operation_description="List all available resume templates",
        manual_parameters=[
            openapi.Parameter(
                'template_type',
                openapi.IN_QUERY,
                description="Filter by template type",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'industry',
                openapi.IN_QUERY,
                description="Filter by industry",
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        responses={200: ResumeTemplateSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        template_type = request.query_params.get('template_type')
        industry = request.query_params.get('industry')
        
        queryset = self.get_queryset()
        
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        if industry:
            queryset = queryset.filter(industry=industry)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ResumeExportView(generics.ListCreateAPIView):
    """List and create resume exports"""
    serializer_class = ResumeExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ResumeExport.objects.none()
        return ResumeExport.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResumeExportCreateSerializer
        return ResumeExportSerializer
    
    @swagger_auto_schema(
        operation_description="List all resume exports for the user",
        responses={200: ResumeExportSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new resume export",
        request_body=ResumeExportCreateSerializer,
        responses={201: ResumeExportSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create export (mock implementation)
        export = serializer.save(user=request.user)
        
        # Mock file generation
        export.file_path = f"/exports/resume_{export.resume.id}_{export.export_format}.{export.export_format}"
        export.file_size = 1024 * 50  # Mock 50KB file
        export.save()
        
        return Response(
            ResumeExportSerializer(export).data,
            status=status.HTTP_201_CREATED
        )

class ResumeExportDetailView(generics.RetrieveAPIView):
    """Get export details and download"""
    serializer_class = ResumeExportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ResumeExport.objects.none()
        return ResumeExport.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Get export details and download link",
        responses={200: ResumeExportSerializer}
    )
    def get(self, request, *args, **kwargs):
        export = self.get_object()
        
        # Update download timestamp
        if not export.downloaded_at:
            export.downloaded_at = timezone.now()
            export.save()
        
        serializer = self.get_serializer(export)
        return Response(serializer.data)

class JobDescriptionListView(generics.ListCreateAPIView):
    """Job Description List and Create View"""
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all job descriptions",
        manual_parameters=[
            openapi.Parameter('source', openapi.IN_QUERY, description="Filter by source", type=openapi.TYPE_STRING),
            openapi.Parameter('company', openapi.IN_QUERY, description="Filter by company", type=openapi.TYPE_STRING),
            openapi.Parameter('job_type', openapi.IN_QUERY, description="Filter by job type", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new job description",
        request_body=JobDescriptionSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class JobDescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Job Description Detail View"""
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

class JobCrawlerView(generics.CreateAPIView):
    """Job Crawler View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Crawl job descriptions from external sources",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'job_title': openapi.Schema(type=openapi.TYPE_STRING, description="Job title to search"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description="Location to search"),
                'sources': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Sources to crawl"),
                'limit': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of jobs to crawl per source"),
            },
            required=['job_title', 'location']
        ),
        responses={
            200: openapi.Response(
                description="Jobs crawled successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'jobs_crawled': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'jobs': JobDescriptionSerializer(many=True)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        job_title = request.data.get('job_title')
        location = request.data.get('location')
        sources = request.data.get('sources', ['indeed'])
        limit = request.data.get('limit', 20)
        
        if not job_title or not location:
            return Response(
                {'error': 'job_title and location are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # JDManager removed - functionality moved to external service
            # jd_manager = JDManager()
            # jobs = jd_manager.crawl_and_process_jobs(job_title, location, sources, limit)
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            jobs = job_crawler_service.crawl_jobs(job_title, location, sources, limit) if hasattr(job_crawler_service, 'crawl_jobs') else []
            
            return Response({
                'message': f'Successfully crawled {len(jobs)} jobs',
                'jobs_crawled': len(jobs),
                'jobs': JobDescriptionSerializer(jobs, many=True).data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error crawling jobs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResumeJobMatchView(generics.ListCreateAPIView):
    """Resume-Job Match View"""
    serializer_class = ResumeJobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        resume_id = self.request.query_params.get('resume_id')
        jd_id = self.request.query_params.get('jd_id')
        
        queryset = ResumeJobMatch.objects.all()
        
        if resume_id:
            queryset = queryset.filter(resume_id=resume_id)
        if jd_id:
            queryset = queryset.filter(job_description_id=jd_id)
        
        return queryset.order_by('-overall_match_score')
    
    @swagger_auto_schema(
        operation_description="List resume-job matches",
        manual_parameters=[
            openapi.Parameter('resume_id', openapi.IN_QUERY, description="Filter by resume ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('jd_id', openapi.IN_QUERY, description="Filter by job description ID", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new resume-job match",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resume_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Resume ID"),
                'jd_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Job Description ID"),
            },
            required=['resume_id', 'jd_id']
        )
    )
    def post(self, request, *args, **kwargs):
        resume_id = request.data.get('resume_id')
        jd_id = request.data.get('jd_id')
        
        if not resume_id or not jd_id:
            return Response(
                {'error': 'resume_id and jd_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # JDManager removed - functionality moved to external service
            # jd_manager = JDManager()
            # match = jd_manager.matcher.match_resume_to_jd(resume_id, jd_id)
            from gateai.external_services.third_party_apis.resume_matcher import resume_matcher_service
            match = resume_matcher_service.match_resume_to_jd(resume_id, jd_id) if hasattr(resume_matcher_service, 'match_resume_to_jd') else None
            
            return Response(
                ResumeJobMatchSerializer(match).data,
                status=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error creating match: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResumeJobMatchDetailView(generics.RetrieveDestroyAPIView):
    """Resume-Job Match Detail View"""
    queryset = ResumeJobMatch.objects.all()
    serializer_class = ResumeJobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

class JobRecommendationView(generics.ListAPIView):
    """Job Recommendation View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get job recommendations for a resume",
        manual_parameters=[
            openapi.Parameter('resume_id', openapi.IN_QUERY, description="Resume ID", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Number of recommendations", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        resume_id = request.query_params.get('resume_id')
        limit = int(request.query_params.get('limit', 10))
        
        if not resume_id:
            return Response(
                {'error': 'resume_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # JDManager removed - functionality moved to external service
            # jd_manager = JDManager()
            # recommendations = jd_manager.get_job_recommendations(resume_id, limit)
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            recommendations = job_crawler_service.get_recommendations(resume_id, limit) if hasattr(job_crawler_service, 'get_recommendations') else []
            
            return Response({
                'resume_id': resume_id,
                'recommendations_count': len(recommendations),
                'recommendations': recommendations
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error getting recommendations: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AutoMatchView(generics.CreateAPIView):
    """Auto Match Resume to Jobs View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Automatically match resume to relevant jobs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resume_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Resume ID"),
                'job_titles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Job titles to search"),
                'locations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Locations to search"),
                'limit': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of jobs to match"),
            },
            required=['resume_id']
        ),
        responses={
            200: openapi.Response(
                description="Auto match completed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'matches_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'matches': ResumeJobMatchSerializer(many=True)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        resume_id = request.data.get('resume_id')
        job_titles = request.data.get('job_titles')
        locations = request.data.get('locations')
        limit = request.data.get('limit', 20)
        
        if not resume_id:
            return Response(
                {'error': 'resume_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # JDManager removed - functionality moved to external service
            # jd_manager = JDManager()
            # matches = jd_manager.match_resume_to_jobs(resume_id, job_titles, locations, limit)
            from gateai.external_services.third_party_apis.resume_matcher import resume_matcher_service
            matches = resume_matcher_service.match_resume_to_jobs(resume_id, job_titles, locations, limit) if hasattr(resume_matcher_service, 'match_resume_to_jobs') else []
            
            return Response({
                'message': f'Successfully created {len(matches)} matches',
                'matches_created': len(matches),
                'matches': ResumeJobMatchSerializer(matches, many=True).data
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error in auto match: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserSubscriptionView(generics.RetrieveUpdateAPIView):
    """User Subscription View"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(UserSubscription, user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Get user subscription and usage statistics"
    )
    def get(self, request, *args, **kwargs):
        tier_service = TierService(request.user)
        usage_stats = tier_service.get_usage_stats()
        
        return Response({
            'subscription': self.get_serializer(self.get_object()).data,
            'usage_stats': usage_stats
        })

class KeywordMatchView(generics.CreateAPIView):
    """Keyword Match View for Free Tier"""
    serializer_class = KeywordMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Analyze resume with keywords (Free Tier)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resume_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Resume ID"),
                'keywords': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Keywords to match"),
                'job_title': openapi.Schema(type=openapi.TYPE_STRING, description="Target job title"),
                'industry': openapi.Schema(type=openapi.TYPE_STRING, description="Target industry"),
            },
            required=['resume_id', 'keywords']
        )
    )
    def post(self, request, *args, **kwargs):
        resume_id = request.data.get('resume_id')
        keywords = request.data.get('keywords', [])
        job_title = request.data.get('job_title')
        industry = request.data.get('industry')
        
        if not resume_id or not keywords:
            return Response(
                {'error': 'resume_id and keywords are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get appropriate service based on user tier
            service = TierFactory.get_service(request.user)
            
            if hasattr(service, 'analyze_resume_with_keywords'):
                # Free tier
                result = service.analyze_resume_with_keywords(resume_id, keywords, job_title, industry)
                return Response(
                    KeywordMatchSerializer(result).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                # Premium/Enterprise tier - use advanced analysis
                return Response(
                    {'error': 'Premium users should use JD matching instead'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error in keyword matching: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PremiumAnalysisView(generics.CreateAPIView):
    """Premium Analysis View for JD Matching"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Analyze resume with job description (Premium Tier)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resume_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Resume ID"),
                'jd_text': openapi.Schema(type=openapi.TYPE_STRING, description="Job description text"),
                'job_title': openapi.Schema(type=openapi.TYPE_STRING, description="Job title"),
                'company': openapi.Schema(type=openapi.TYPE_STRING, description="Company name"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description="Job location"),
            },
            required=['resume_id', 'jd_text', 'job_title', 'company', 'location']
        )
    )
    def post(self, request, *args, **kwargs):
        resume_id = request.data.get('resume_id')
        jd_text = request.data.get('jd_text')
        job_title = request.data.get('job_title')
        company = request.data.get('company')
        location = request.data.get('location')
        
        if not all([resume_id, jd_text, job_title, company, location]):
            return Response(
                {'error': 'All fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get premium service
            service = TierFactory.get_service(request.user)
            
            if hasattr(service, 'analyze_resume_with_jd'):
                # Premium tier
                result = service.analyze_resume_with_jd(resume_id, jd_text, job_title, company, location)
                return Response(
                    ResumeJobMatchSerializer(result).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': 'Premium tier required for JD matching'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error in JD analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FeedbackView(generics.UpdateAPIView):
    """Feedback View for Premium Users"""
    queryset = ResumeJobMatch.objects.all()
    serializer_class = ResumeJobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Provide feedback on match accuracy (Premium Tier)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'feedback_text': openapi.Schema(type=openapi.TYPE_STRING, description="Feedback text"),
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description="Rating (1-5)"),
            },
            required=['feedback_text', 'rating']
        )
    )
    def patch(self, request, *args, **kwargs):
        match_id = kwargs.get('pk')
        feedback_text = request.data.get('feedback_text')
        rating = request.data.get('rating')
        
        if not feedback_text or not rating:
            return Response(
                {'error': 'feedback_text and rating are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not 1 <= rating <= 5:
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get premium service
            service = TierFactory.get_service(request.user)
            
            if hasattr(service, 'provide_feedback'):
                result = service.provide_feedback(match_id, feedback_text, rating)
                return Response(
                    ResumeJobMatchSerializer(result).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Premium tier required for feedback'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error providing feedback: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ExternalAPIConfigView removed - functionality moved to ExternalServiceIntegration
    
    @swagger_auto_schema(
        operation_description="List external API configurations (Enterprise Tier)"
    )
    def get(self, request, *args, **kwargs):
        # Check if user has enterprise access
        tier_service = TierService(request.user)
        if tier_service.subscription.tier != 'enterprise':
            return Response(
                {'error': 'Enterprise tier required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create external API configuration (Enterprise Tier)"
    )
    def post(self, request, *args, **kwargs):
        # Check if user has enterprise access
        tier_service = TierService(request.user)
        if tier_service.subscription.tier != 'enterprise':
            return Response(
                {'error': 'Enterprise tier required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().post(request, *args, **kwargs)

class BatchAnalysisView(generics.CreateAPIView):
    """Batch Analysis View (Enterprise Tier)"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Batch analyze resumes against JDs (Enterprise Tier)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'resume_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description="Resume IDs"),
                'jd_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description="Job Description IDs"),
            },
            required=['resume_ids', 'jd_ids']
        )
    )
    def post(self, request, *args, **kwargs):
        resume_ids = request.data.get('resume_ids', [])
        jd_ids = request.data.get('jd_ids', [])
        
        if not resume_ids or not jd_ids:
            return Response(
                {'error': 'resume_ids and jd_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if user has enterprise access
            tier_service = TierService(request.user)
            if tier_service.subscription.tier != 'enterprise':
                return Response(
                    {'error': 'Enterprise tier required for batch analysis'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get enterprise service
            service = TierFactory.get_service(request.user)
            results = service.batch_analyze_resumes(resume_ids, jd_ids)
            
            return Response({
                'message': f'Batch analysis completed for {len(resume_ids)} resumes and {len(jd_ids)} JDs',
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error in batch analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReferralStatsView(generics.RetrieveAPIView):
    """Referral Statistics View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user referral statistics and rewards"
    )
    def get(self, request, *args, **kwargs):
        referral_service = ReferralService()
        stats = referral_service.get_user_stats(request.user)
        
        return Response(stats)

class CreateInvitationView(generics.CreateAPIView):
    """Create Invitation View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create invitation for a friend",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Email of the person to invite"),
            },
            required=['email']
        )
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            referral_service = ReferralService()
            invitation = referral_service.create_invitation(request.user, email)
            
            return Response({
                'message': f'Invitation sent to {email}',
                'invitation': {
                    'code': invitation.code,
                    'email': invitation.email,
                    'expires_at': invitation.expires_at,
                    'reward_days': invitation.inviter_reward_days
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error creating invitation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UseInvitationView(generics.CreateAPIView):
    """Use Invitation View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Use invitation code during registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="Invitation code"),
            },
            required=['code']
        )
    )
    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Invitation code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            referral_service = ReferralService()
            success = referral_service.use_invitation(code, request.user)
            
            if success:
                # Get invitation details
                invitation = InvitationCode.objects.get(code=code)
                
                return Response({
                    'message': 'Invitation used successfully!',
                    'reward_days': invitation.invitee_reward_days,
                    'inviter': invitation.inviter.username
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to use invitation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error using invitation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReferralLinkView(generics.RetrieveAPIView):
    """Referral Link View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's referral link for sharing"
    )
    def get(self, request, *args, **kwargs):
        referral_service = ReferralService()
        referral_link = referral_service.get_referral_link(request.user)
        
        return Response({
            'referral_link': referral_link,
            'username': request.user.username
        })

class PricingView(generics.ListAPIView):
    """Pricing Information View"""
    
    @swagger_auto_schema(
        operation_description="Get pricing information for all tiers"
    )
    def get(self, request, *args, **kwargs):
        pricing = PricingService.get_pricing()
        feature_comparison = PricingService.get_feature_comparison()
        
        return Response({
            'pricing': pricing,
            'feature_comparison': feature_comparison,
            'currency': 'USD'
        })

class PricingDetailView(generics.RetrieveAPIView):
    """Pricing Detail View"""
    
    @swagger_auto_schema(
        operation_description="Get detailed pricing for specific tier",
        manual_parameters=[
            openapi.Parameter('tier', openapi.IN_PATH, description="Tier name", type=openapi.TYPE_STRING, required=True),
        ]
    )
    def get(self, request, *args, **kwargs):
        tier = kwargs.get('tier', 'free')
        pricing = PricingService.get_pricing(tier)
        
        if not pricing:
            return Response(
                {'error': 'Invalid tier'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate savings for yearly billing
        monthly_savings = PricingService.calculate_savings(tier, 'yearly')
        
        return Response({
            'tier': tier,
            'pricing': pricing,
            'savings': monthly_savings,
            'currency': 'USD'
        })

class SubscriptionUpgradeView(generics.UpdateAPIView):
    """Subscription Upgrade View"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(UserSubscription, user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Upgrade user subscription",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'tier': openapi.Schema(type=openapi.TYPE_STRING, description="New tier", enum=['free', 'premium', 'enterprise']),
                'billing_cycle': openapi.Schema(type=openapi.TYPE_STRING, description="Billing cycle", enum=['monthly', 'yearly']),
            },
            required=['tier', 'billing_cycle']
        )
    )
    def patch(self, request, *args, **kwargs):
        tier = request.data.get('tier')
        billing_cycle = request.data.get('billing_cycle')
        
        if not tier or not billing_cycle:
            return Response(
                {'error': 'tier and billing_cycle are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if tier not in ['free', 'premium', 'enterprise']:
            return Response(
                {'error': 'Invalid tier'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if billing_cycle not in ['monthly', 'yearly']:
            return Response(
                {'error': 'Invalid billing cycle'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = self.get_object()
            
            # Get pricing information
            pricing = PricingService.get_pricing(tier)
            
            # Update subscription
            subscription.tier = tier
            subscription.billing_cycle = billing_cycle
            subscription.monthly_price = pricing['monthly_price']
            subscription.yearly_price = pricing['yearly_price']
            
            # Set subscription end date
            if tier == 'free':
                subscription.subscription_end = None
            else:
                if billing_cycle == 'monthly':
                    subscription.subscription_end = timezone.now() + timezone.timedelta(days=30)
                else:
                    subscription.subscription_end = timezone.now() + timezone.timedelta(days=365)
            
            subscription.save()
            
            return Response({
                'message': f'Successfully upgraded to {tier} tier',
                'subscription': UserSubscriptionSerializer(subscription).data,
                'pricing': pricing
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error upgrading subscription: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FreeDaysUsageView(generics.CreateAPIView):
    """Free Days Usage View"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Use free days earned through referrals",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'days': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of days to use"),
            },
            required=['days']
        )
    )
    def post(self, request, *args, **kwargs):
        days = request.data.get('days')
        
        if not days or days <= 0:
            return Response(
                {'error': 'Valid number of days is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            
            if subscription.use_free_days(days):
                return Response({
                    'message': f'Successfully used {days} free days',
                    'available_free_days': subscription.available_free_days,
                    'free_days_used': subscription.free_days_used
                })
            else:
                return Response(
                    {'error': 'Not enough free days available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error using free days: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DataDeletionRequestView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Create a data deletion request")
    def post(self, request, *args, **kwargs):
        _require_student(request)
        tok = secrets.token_hex(16)
        req = DataDeletionRequest.objects.create(user=request.user, token=tok)
        return Response({'request_id': req.id, 'token': req.token, 'status': req.status})


class DataDeletionRequestListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DataDeletionRequestSerializer

    def get_queryset(self):
        _require_student(self.request)
        return DataDeletionRequest.objects.filter(user=self.request.user).order_by('-requested_at')


class LegalDisclaimerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LegalDisclaimerSerializer

    def get_queryset(self):
        _require_student(self.request)
        return LegalDisclaimer.objects.filter(is_active=True).order_by('-effective_date')


class LegalDisclaimerDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LegalDisclaimerSerializer
    lookup_field = 'disclaimer_type'

    def get_object(self):
        _require_student(self.request)
        return get_object_or_404(
            LegalDisclaimer,
            disclaimer_type=self.kwargs['disclaimer_type'],
            is_active=True
        )


class DataConsentView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        _require_student(request)
        data_consents = UserDataConsent.objects.filter(user=request.user)
        disclaimer_consents = UserDisclaimerConsent.objects.filter(user=request.user).select_related('disclaimer')
        required = LegalComplianceManager.get_required_disclaimers(request.user)

        return Response({
            'data_consents': UserDataConsentSerializer(data_consents, many=True).data,
            'disclaimer_consents': UserDisclaimerConsentSerializer(disclaimer_consents, many=True).data,
            'required_disclaimers': LegalDisclaimerSerializer(required, many=True).data,
        })

    @swagger_auto_schema(
        operation_description="Grant data processing consent and optional disclaimer consents",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'consent_type': openapi.Schema(type=openapi.TYPE_STRING, description="Consent type"),
                'consent_version': openapi.Schema(type=openapi.TYPE_STRING, description="Consent version"),
                'disclaimer_types': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Disclaimer types to record consent for"
                ),
            },
        )
    )
    def post(self, request, *args, **kwargs):
        _require_student(request)
        consent_type = request.data.get('consent_type', 'data_processing')
        consent_version = request.data.get('consent_version', '1.0')
        disclaimer_types = request.data.get('disclaimer_types', [])

        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        DataConsentManager.grant_consent(
            request.user,
            consent_type,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_version=consent_version
        )

        if disclaimer_types:
            for disclaimer_type in disclaimer_types:
                disclaimer = LegalComplianceManager.get_active_disclaimer(disclaimer_type)
                if disclaimer:
                    LegalComplianceManager.record_disclaimer_consent(
                        request.user,
                        disclaimer,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )

        return self.get(request, *args, **kwargs)


class RevokeConsentView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Revoke data processing or disclaimer consent",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'consent_type': openapi.Schema(type=openapi.TYPE_STRING, description="Consent type to revoke"),
                'disclaimer_type': openapi.Schema(type=openapi.TYPE_STRING, description="Disclaimer type to revoke"),
            },
        )
    )
    def post(self, request, *args, **kwargs):
        _require_student(request)
        consent_type = request.data.get('consent_type')
        disclaimer_type = request.data.get('disclaimer_type')

        if consent_type:
            DataConsentManager.revoke_consent(request.user, consent_type)

        if disclaimer_type:
            disclaimer = LegalComplianceManager.get_active_disclaimer(disclaimer_type)
            if disclaimer:
                UserDisclaimerConsent.objects.filter(
                    user=request.user,
                    disclaimer=disclaimer
                ).delete()

        return Response({'status': 'ok'})


class DataDeletionVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Verify a data deletion request by token")
    def post(self, request, request_id, token, *args, **kwargs):
        _require_student(request)
        req = get_object_or_404(DataDeletionRequest, id=request_id, user=request.user)
        if req.token != token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        req.status = 'verified'
        req.verified_at = timezone.now()
        req.save()
        return Response({'request_id': req.id, 'status': req.status})


class DataDeletionStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        _require_student(request)
        latest = DataDeletionRequest.objects.filter(user=request.user).order_by('-requested_at').first()
        if not latest:
            return Response({'status': 'none'})
        return Response({'request_id': latest.id, 'status': latest.status})


class PrivacyRightsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        _require_student(request)
        return Response({'rights': ['access', 'rectification', 'erasure', 'portability', 'restriction', 'objection']})


class DataExportView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        _require_student(request)
        job = DataExportJob.objects.create(user=request.user)
        try:
            # Tasks module not yet implemented - using placeholder
            # from ats_signals.tasks import build_user_data_export
            # build_user_data_export.delay(job.id)
            # For now, mark as processing
            job.status = 'processing'
            job.save()
        except Exception:
            # fallback: mark as failed if task system not available
            job.status = 'failed'
            job.save()
        return Response({'job_id': job.id, 'status': job.status}, status=status.HTTP_202_ACCEPTED)

class DataExportStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        _require_student(request)
        job = DataExportJob.objects.filter(user=request.user).order_by('-requested_at').first()
        if not job:
            return Response({'status': 'none'})
        # Optionally presign S3 URLs when USE_S3 is enabled
        download_url = job.download_url
        try:
            from django.conf import settings as dj_settings
            if getattr(dj_settings, 'USE_S3', False) and download_url and download_url.startswith('https://'):
                import boto3, os
                s3 = boto3.client('s3', region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'))
                bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME')
                key = download_url.split(f"https://{bucket}.s3.amazonaws.com/")[-1]
                presigned = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=600
                )
                download_url = presigned
        except Exception:
            pass
        return Response({'job_id': job.id, 'status': job.status, 'download_url': download_url})


# JobCrawler API proxy views
class JobCrawlerSearchView(generics.GenericAPIView):
    """Direct proxy to JobCrawler search endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Extract query parameters
        query = request.GET.get('query', 'python developer')
        location = request.GET.get('location', 'San Francisco')
        limit = int(request.GET.get('limit', 5))
        
        try:
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            result = job_crawler_service.search_jobs(
                query=query,
                filters={'location': location},
                page=1,
                user=request.user
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobCrawlerTrendingView(generics.GenericAPIView):
    """Direct proxy to JobCrawler trending jobs endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            result = job_crawler_service.get_trending_jobs(user=request.user)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobCrawlerSalaryView(generics.GenericAPIView):
    """Direct proxy to JobCrawler salary data endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        job_title = request.GET.get('job_title', 'Software Engineer')
        location = request.GET.get('location', 'San Francisco')
        
        try:
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            result = job_crawler_service.get_salary_data(
                job_title=job_title,
                location=location,
                user=request.user
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobCrawlerSkillsView(generics.GenericAPIView):
    """Direct proxy to JobCrawler skills data endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        job_title = request.GET.get('job_title', 'Data Scientist')
        location = request.GET.get('location', 'New York')
        
        try:
            from gateai.external_services.third_party_apis.job_crawler import job_crawler_service
            result = job_crawler_service.get_skill_demand(
                job_title=job_title,
                location=location,
                user=request.user
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ATSSignalListView(generics.ListAPIView):
    """
    List ATS Signals for a DecisionSlot.
    
    GET /api/v1/ats-signals/?decision_slot_id=<id>
    
    Object-level permissions: Users can only access signals for decision slots they own.
    Staff/admin can access all signals.
    """
    from .serializers import ATSSignalSerializer
    
    serializer_class = ATSSignalSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ATSSignal.objects.all()
    
    def get_queryset(self):
        decision_slot_id = self.request.query_params.get('decision_slot_id')
        
        # Apply object-level permissions: filter to user's allowed decision slots
        queryset = filter_signals_by_ownership(ATSSignal.objects.all(), self.request.user)
        
        # If specific decision_slot_id requested, check access and filter
        if decision_slot_id:
            # Check if user can access this decision slot
            if not user_can_access_decision_slot(self.request.user, decision_slot_id):
                # Return 404 to avoid leaking existence
                from django.http import Http404
                raise Http404("Decision slot not found or access denied")
            
            queryset = queryset.filter(decision_slot_id=decision_slot_id)
        
        # Optional: filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Optional: filter by signal_type
        signal_type = self.request.query_params.get('signal_type')
        if signal_type:
            queryset = queryset.filter(signal_type=signal_type)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Return signals grouped by severity"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Group by severity for frontend
        grouped = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': [],
        }
        
        for signal in serializer.data:
            severity = signal.get('severity', 'info')
            if severity in grouped:
                grouped[severity].append(signal)
        
        return Response({
            'decision_slot_id': request.query_params.get('decision_slot_id'),
            'signals': serializer.data,
            'grouped_by_severity': grouped,
            'total_count': len(serializer.data),
            'critical_count': len(grouped['critical']),
            'high_count': len(grouped['high']),
        })


class ATSSignalDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single ATS Signal.
    
    GET /api/v1/ats-signals/<id>/
    
    Object-level permissions: Users can only access signals for decision slots they own.
    Staff/admin can access all signals.
    """
    from .serializers import ATSSignalSerializer
    
    serializer_class = ATSSignalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Apply object-level permissions: filter to user's allowed decision slots
        return filter_signals_by_ownership(ATSSignal.objects.all(), self.request.user)
