import os
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Resume, ResumeAnalysis, ResumeFeedback,
    ResumeComparison, ResumeTemplate, ResumeExport,
    JobDescription, ResumeJobMatch, KeywordMatch, UserSubscription, InvitationCode,
    UserDataConsent, LegalDisclaimer, UserDisclaimerConsent, DataDeletionRequest,
    ATSSignal
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for resume-related operations"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'avatar')
        ref_name = "ResumeUserSerializer"

class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model"""
    user = UserSerializer(read_only=True)
    file_size_display = serializers.SerializerMethodField()
    is_analyzed = serializers.ReadOnlyField()
    has_analysis = serializers.ReadOnlyField()

    class Meta:
        model = Resume
        fields = (
            'id', 'user', 'title', 'file', 'status', 'file_size', 'file_size_display',
            'file_type', 'uploaded_at', 'analyzed_at', 'is_analyzed', 'has_analysis',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'status', 'file_size', 'file_type', 'uploaded_at', 'analyzed_at', 'created_at', 'updated_at')

    def get_file_size_display(self, obj):
        """Get human readable file size"""
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            else:
                size_mb = size_kb / 1024
                return f"{size_mb:.1f} MB"
        return "N/A"

    def create(self, validated_data):
        """Create resume with file size calculation"""
        file = validated_data.get('file')
        if file:
            validated_data['file_size'] = file.size
            validated_data['file_type'] = file.name.split('.')[-1].lower()

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ResumeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating resumes"""
    class Meta:
        model = Resume
        fields = ('title', 'file')

    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")

        # Check file type
        allowed_types = ['pdf', 'doc', 'docx']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_types:
            raise serializers.ValidationError("Only PDF, DOC, and DOCX files are allowed")

        header = value.read(8)
        value.seek(0)
        if file_extension == 'pdf' and not header.startswith(b'%PDF-'):
            raise serializers.ValidationError("Invalid PDF file signature")
        if file_extension == 'docx' and not header.startswith(b'PK'):
            raise serializers.ValidationError("Invalid DOCX file signature")
        if file_extension == 'doc' and not header.startswith(b'\xD0\xCF\x11\xE0'):
            raise serializers.ValidationError("Invalid DOC file signature")

        if os.environ.get('CLAMAV_ENABLED', '').lower() == 'true':
            try:
                import clamd
            except Exception:
                raise serializers.ValidationError("Virus scanner not available")

            try:
                scanner = clamd.ClamdUnixSocket()
                scan_result = scanner.instream(value)
                value.seek(0)
                if scan_result and scan_result.get('stream', [None, 'OK'])[1] != 'OK':
                    raise serializers.ValidationError("File failed virus scan")
            except serializers.ValidationError:
                raise
            except Exception:
                raise serializers.ValidationError("Virus scan failed")

        return value

    def create(self, validated_data):
        """Create resume with file metadata"""
        file = validated_data.get('file')
        if file:
            validated_data['file_size'] = file.size
            validated_data['file_type'] = file.name.split('.')[-1].lower()

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for ResumeAnalysis model"""
    resume = ResumeSerializer(read_only=True)
    score_category = serializers.ReadOnlyField()

    class Meta:
        model = ResumeAnalysis
        fields = (
            'id', 'resume', 'overall_score', 'structure_score', 'content_score',
            'keyword_score', 'ats_score', 'detected_keywords',
            'missing_keywords', 'industry_keywords', 'technical_skills', 'soft_skills',
            'skill_gaps', 'experience_years', 'job_titles', 'companies',
            'education_level', 'institutions', 'certifications', 'analysis_version',
            'processing_time', 'confidence_score', 'score_category', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

class ResumeFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for ResumeFeedback model"""
    analysis = ResumeAnalysisSerializer(read_only=True)

    class Meta:
        model = ResumeFeedback
        fields = (
            'id', 'analysis', 'summary', 'strengths', 'weaknesses',
            'structure_recommendations', 'content_recommendations',
            'keyword_recommendations', 'format_recommendations',
            'industry_insights', 'market_trends', 'salary_insights',
            'priority_actions', 'quick_fixes', 'long_term_improvements',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

class ResumeComparisonSerializer(serializers.ModelSerializer):
    """Serializer for ResumeComparison model"""
    user = UserSerializer(read_only=True)
    resume_count = serializers.SerializerMethodField()

    class Meta:
        model = ResumeComparison
        fields = (
            'id', 'user', 'title', 'description', 'resume_count',
            'overall_improvement', 'improvement_areas', 'maintained_strengths',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def get_resume_count(self, obj):
        return obj.resumes.count()

class ResumeComparisonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating resume comparisons"""
    class Meta:
        model = ResumeComparison
        fields = ('title', 'description', 'resumes')

    def validate(self, data):
        """Validate comparison data"""
        resumes = data.get('resumes', [])
        
        if len(resumes) < 2:
            raise serializers.ValidationError("At least 2 resumes are required for comparison")

        for resume in resumes:
            if resume.user != self.context['request'].user:
                raise serializers.ValidationError("You can only compare your own resumes")

        return data

class ResumeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ResumeTemplate model"""
    class Meta:
        model = ResumeTemplate
        fields = (
            'id', 'name', 'description', 'template_type', 'industry',
            'html_template', 'css_styles', 'is_active', 'is_premium',
            'usage_count', 'preview_image', 'created_at', 'updated_at'
        )
        read_only_fields = ('usage_count', 'created_at', 'updated_at')

class ResumeExportSerializer(serializers.ModelSerializer):
    """Serializer for ResumeExport model"""
    resume = ResumeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    template_used = ResumeTemplateSerializer(read_only=True)
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = ResumeExport
        fields = (
            'id', 'resume', 'user', 'export_format', 'file_path', 'file_size',
            'file_size_display', 'template_used', 'customizations',
            'created_at', 'downloaded_at'
        )
        read_only_fields = ('user', 'file_path', 'file_size', 'created_at', 'downloaded_at')

    def get_file_size_display(self, obj):
        """Get human readable file size"""
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb < 1024:
                return f"{size_kb:.1f} KB"
            else:
                size_mb = size_kb / 1024
                return f"{size_mb:.1f} MB"
        return "N/A"

class ResumeExportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating resume exports"""
    class Meta:
        model = ResumeExport
        fields = ('resume', 'export_format', 'template_used', 'customizations')

    def validate(self, data):
        """Validate export data"""
        resume = data.get('resume')
        user = self.context['request'].user

        if resume.user != user:
            raise serializers.ValidationError("You can only export your own resumes")

        return data

# Request/Response serializers for API operations
class ResumeAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for resume analysis requests"""
    resume_id = serializers.IntegerField(help_text="ID of the resume to analyze")
    industry = serializers.CharField(max_length=50, required=False, help_text="Target industry for analysis")
    job_title = serializers.CharField(max_length=100, required=False, help_text="Target job title for analysis")
    consent = serializers.BooleanField(required=False, default=False, help_text="User consent to data processing and AI analysis")
    consent_version = serializers.CharField(max_length=10, required=False, default="1.0", help_text="Consent policy version")

class ResumeSearchSerializer(serializers.Serializer):
    """Serializer for resume search requests"""
    query = serializers.CharField(max_length=200, required=False, help_text="Search query")
    status = serializers.ChoiceField(choices=Resume.STATUS_CHOICES, required=False, help_text="Filter by status")
    date_from = serializers.DateField(required=False, help_text="Filter by upload date from")
    date_to = serializers.DateField(required=False, help_text="Filter by upload date to")

class ResumeFilterSerializer(serializers.Serializer):
    """Serializer for resume filtering"""
    status = serializers.ChoiceField(choices=Resume.STATUS_CHOICES, required=False)
    file_type = serializers.CharField(max_length=50, required=False)
    has_analysis = serializers.BooleanField(required=False)
    date_range = serializers.CharField(max_length=20, required=False, help_text="Date range: today, week, month, year")

class ResumeStatsSerializer(serializers.Serializer):
    """Serializer for resume statistics"""
    total_resumes = serializers.IntegerField()
    analyzed_resumes = serializers.IntegerField()
    pending_analysis = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    score_distribution = serializers.DictField()
    recent_uploads = serializers.ListField()

class ResumeAnalysisResultSerializer(serializers.Serializer):
    """Serializer for resume analysis results"""
    resume = ResumeSerializer()
    analysis = ResumeAnalysisSerializer()
    feedback = ResumeFeedbackSerializer()
    processing_time = serializers.DecimalField(max_digits=5, decimal_places=2)
    analysis_status = serializers.CharField(max_length=20)

class JobDescriptionSerializer(serializers.ModelSerializer):
    """Job Description Serializer"""

    class Meta:
        model = JobDescription
        fields = [
            'id', 'title', 'company', 'location', 'description',
            'required_skills', 'preferred_skills', 'experience_level',
            'education_level', 'salary_range', 'job_type', 'source',
            'source_url', 'is_processed', 'created_at',
            'updated_at', 'total_skills', 'skill_density'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_skills', 'skill_density']

class JobDescriptionCreateSerializer(serializers.ModelSerializer):
    """Job Description Create Serializer"""

    class Meta:
        model = JobDescription
        fields = [
            'title', 'company', 'location', 'description',
            'required_skills', 'preferred_skills', 'experience_level',
            'education_level', 'salary_range', 'job_type', 'source_url'
        ]

    def validate_required_skills(self, value):
        """Validate required skills"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Required skills must be a list")
        return value

    def validate_preferred_skills(self, value):
        """Validate preferred skills"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred skills must be a list")
        return value

class ResumeJobMatchSerializer(serializers.ModelSerializer):
    """Resume-Job Match Serializer"""

    resume_title = serializers.CharField(source='resume.title', read_only=True)
    job_title = serializers.CharField(source='job_description.title', read_only=True)
    company_name = serializers.CharField(source='job_description.company', read_only=True)
    job_location = serializers.CharField(source='job_description.location', read_only=True)

    class Meta:
        model = ResumeJobMatch
        fields = [
            'id', 'resume', 'job_description', 'resume_title', 'job_title',
            'company_name', 'job_location', 'overall_match_score',
            'skill_match_score', 'experience_match_score', 'education_match_score',
            'matched_skills', 'missing_skills', 'skill_gaps', 'match_level',
            'match_recommendations', 'created_at', 'updated_at',
            'is_excellent_match', 'is_good_match', 'is_fair_match', 'is_poor_match'
        ]
        read_only_fields = [
            'id', 'overall_match_score', 'skill_match_score', 'experience_match_score',
            'education_match_score', 'matched_skills', 'missing_skills', 'skill_gaps',
            'match_level', 'match_recommendations', 'created_at', 'updated_at',
            'is_excellent_match', 'is_good_match', 'is_fair_match', 'is_poor_match'
        ]

class ResumeJobMatchCreateSerializer(serializers.ModelSerializer):
    """Resume-Job Match Create Serializer"""

    class Meta:
        model = ResumeJobMatch
        fields = ['resume', 'job_description']

    def validate(self, data):
        """Validate match data"""
        resume = data.get('resume')
        job_description = data.get('job_description')

        # Check if resume has analysis
        if not resume.has_analysis:
            raise serializers.ValidationError("Resume must be analyzed before matching")

        # Check if match already exists
        if ResumeJobMatch.objects.filter(resume=resume, job_description=job_description).exists():
            raise serializers.ValidationError("Match already exists")

        return data


class ExternalJobCrawlRequestSerializer(serializers.Serializer):
    """Serializer for triggering external job crawler"""
    job_title = serializers.CharField()
    location = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField(), required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)


class ExternalResumeMatchRequestSerializer(serializers.Serializer):
    """Serializer for matching a resume to a job description via external service"""
    resume_id = serializers.IntegerField()
    job_description_id = serializers.IntegerField()

class JobRecommendationSerializer(serializers.Serializer):
    """Job Recommendation Serializer"""

    job = JobDescriptionSerializer()
    match_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    match_level = serializers.CharField()
    matched_skills = serializers.ListField(child=serializers.CharField())
    missing_skills = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.ListField()

class JobCrawlerRequestSerializer(serializers.Serializer):
    """Job Crawler Request Serializer"""

    job_title = serializers.CharField(max_length=200)
    location = serializers.CharField(max_length=200)
    sources = serializers.ListField(
        child=serializers.ChoiceField(choices=['indeed', 'linkedin', 'glassdoor']),
        default=['indeed']
    )
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)

class AutoMatchRequestSerializer(serializers.Serializer):
    """Auto Match Request Serializer"""

    resume_id = serializers.IntegerField()
    job_titles = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False
    )
    locations = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False
    )
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User Subscription Serializer"""

    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'tier', 'subscription_start', 'subscription_end',
            'is_active', 'monthly_resume_uploads', 'monthly_analyses',
            'monthly_jd_matches', 'current_month_uploads', 'current_month_analyses',
            'current_month_matches', 'last_reset_date'
        ]
        read_only_fields = ['id', 'user', 'subscription_start', 'last_reset_date']

class KeywordMatchSerializer(serializers.ModelSerializer):
    """Keyword Match Serializer"""

    resume_title = serializers.CharField(source='resume.title', read_only=True)

    class Meta:
        model = KeywordMatch
        fields = [
            'id', 'user', 'resume', 'resume_title', 'target_keywords',
            'target_job_title', 'target_industry', 'keyword_match_score',
            'matched_keywords', 'missing_keywords', 'basic_recommendations',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'keyword_match_score', 'matched_keywords',
            'missing_keywords', 'basic_recommendations', 'created_at', 'updated_at'
        ]

# ExternalAPIConfigSerializer removed - functionality moved to ExternalServiceIntegration

class InvitationCodeSerializer(serializers.ModelSerializer):
    """Invitation Code Serializer"""

    inviter_username = serializers.CharField(source='inviter.username', read_only=True)
    invitee_username = serializers.CharField(source='invitee.username', read_only=True)

    class Meta:
        model = InvitationCode
        fields = [
            'id', 'inviter', 'inviter_username', 'invitee', 'invitee_username',
            'code', 'email', 'is_used', 'is_expired', 'inviter_reward_days',
            'invitee_reward_days', 'created_at', 'used_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'inviter', 'inviter_username', 'invitee', 'invitee_username',
            'code', 'is_used', 'is_expired', 'inviter_reward_days',
            'invitee_reward_days', 'created_at', 'used_at', 'expires_at'
        ]


class UserDataConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDataConsent
        fields = (
            'id', 'consent_type', 'is_granted', 'granted_at',
            'revoked_at', 'consent_version', 'ip_address', 'user_agent'
        )


class LegalDisclaimerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDisclaimer
        fields = (
            'id', 'disclaimer_type', 'title', 'content', 'version',
            'effective_date', 'requires_consent'
        )


class UserDisclaimerConsentSerializer(serializers.ModelSerializer):
    disclaimer = LegalDisclaimerSerializer(read_only=True)

    class Meta:
        model = UserDisclaimerConsent
        fields = ('id', 'disclaimer', 'consented_at', 'ip_address', 'user_agent')


class DataDeletionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDeletionRequest
        fields = ('id', 'status', 'requested_at', 'verified_at', 'processed_at')


class ATSSignalSerializer(serializers.ModelSerializer):
    """Serializer for ATS Signal model"""
    is_critical = serializers.ReadOnlyField()
    is_high_priority = serializers.ReadOnlyField()
    
    class Meta:
        from .models import ATSSignal
        model = ATSSignal
        fields = (
            'id', 'decision_slot_id', 'signal_type', 'severity', 'category',
            'message', 'details', 'section', 'line_number', 'engine_name',
            'engine_version', 'signal_schema_version', 'is_critical',
            'is_high_priority', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
