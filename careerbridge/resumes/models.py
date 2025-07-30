from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class UserSubscription(models.Model):
    """User subscription model for tier management"""
    
    TIER_CHOICES = (
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    subscription_start = models.DateTimeField(auto_now_add=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Pricing information
    monthly_price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    yearly_price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    billing_cycle = models.CharField(max_length=10, default='monthly', choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])
    
    # Usage limits
    monthly_resume_uploads = models.PositiveIntegerField(default=3)  # Free tier limit
    monthly_analyses = models.PositiveIntegerField(default=5)  # Free tier limit
    monthly_jd_matches = models.PositiveIntegerField(default=10)  # Free tier limit
    
    # Current month usage
    current_month_uploads = models.PositiveIntegerField(default=0)
    current_month_analyses = models.PositiveIntegerField(default=0)
    current_month_matches = models.PositiveIntegerField(default=0)
    
    # Reset date for monthly limits
    last_reset_date = models.DateField(auto_now_add=True)
    
    # Invitation rewards
    free_days_earned = models.PositiveIntegerField(default=0, help_text="Free days earned through invitations")
    free_days_used = models.PositiveIntegerField(default=0, help_text="Free days used")
    
    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"
    
    def __str__(self):
        return f"{self.user.username} - {self.tier}"
    
    def can_upload_resume(self):
        """Check if user can upload resume"""
        if self.tier == 'free':
            return self.current_month_uploads < self.monthly_resume_uploads
        return True
    
    def can_analyze_resume(self):
        """Check if user can analyze resume"""
        if self.tier == 'free':
            return self.current_month_analyses < self.monthly_analyses
        return True
    
    def can_match_jd(self):
        """Check if user can match JD"""
        if self.tier == 'free':
            return self.current_month_matches < self.monthly_jd_matches
        return True
    
    def increment_upload_count(self):
        """Increment upload count"""
        self.current_month_uploads += 1
        self.save()
    
    def increment_analysis_count(self):
        """Increment analysis count"""
        self.current_month_analyses += 1
        self.save()
    
    def increment_match_count(self):
        """Increment match count"""
        self.current_month_matches += 1
        self.save()
    
    def add_free_days(self, days):
        """Add free days earned through invitations"""
        self.free_days_earned += days
        self.save()
    
    def use_free_days(self, days):
        """Use free days"""
        if self.free_days_earned - self.free_days_used >= days:
            self.free_days_used += days
            self.save()
            return True
        return False
    
    @property
    def available_free_days(self):
        """Get available free days"""
        return self.free_days_earned - self.free_days_used

class InvitationCode(models.Model):
    """Invitation code model for referral system"""
    
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invitations', null=True, blank=True)
    
    # Code details
    code = models.CharField(max_length=20, unique=True, help_text="Unique invitation code")
    email = models.EmailField(help_text="Email of the person being invited")
    
    # Status
    is_used = models.BooleanField(default=False, help_text="Whether the invitation has been used")
    is_expired = models.BooleanField(default=False, help_text="Whether the invitation has expired")
    
    # Rewards
    inviter_reward_days = models.PositiveIntegerField(default=7, help_text="Free days for inviter")
    invitee_reward_days = models.PositiveIntegerField(default=7, help_text="Free days for invitee")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When the invitation expires")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.inviter.username} -> {self.email} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    
    def generate_code(self):
        """Generate unique invitation code"""
        while True:
            code = str(uuid.uuid4())[:8].upper()
            if not InvitationCode.objects.filter(code=code).exists():
                return code
    
    def is_valid(self):
        """Check if invitation is still valid"""
        return not self.is_used and not self.is_expired and timezone.now() < self.expires_at
    
    def use_invitation(self, invitee_user):
        """Use the invitation"""
        if not self.is_valid():
            return False
        
        self.invitee = invitee_user
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
        
        # Give rewards
        self.give_rewards()
        
        return True
    
    def give_rewards(self):
        """Give rewards to both inviter and invitee"""
        # Reward inviter
        inviter_subscription, _ = UserSubscription.objects.get_or_create(
            user=self.inviter,
            defaults={'tier': 'free'}
        )
        inviter_subscription.add_free_days(self.inviter_reward_days)
        
        # Reward invitee
        invitee_subscription, _ = UserSubscription.objects.get_or_create(
            user=self.invitee,
            defaults={'tier': 'free'}
        )
        invitee_subscription.add_free_days(self.invitee_reward_days)

class ReferralProgram(models.Model):
    """Referral program configuration"""
    
    name = models.CharField(max_length=100, help_text="Program name")
    is_active = models.BooleanField(default=True, help_text="Whether the program is active")
    
    # Invitation settings
    max_invitations_per_user = models.PositiveIntegerField(default=10, help_text="Maximum invitations per user")
    invitation_expiry_days = models.PositiveIntegerField(default=30, help_text="Days until invitation expires")
    
    # Reward settings
    inviter_reward_days = models.PositiveIntegerField(default=7, help_text="Free days for inviter")
    invitee_reward_days = models.PositiveIntegerField(default=7, help_text="Free days for invitee")
    
    # Milestone rewards
    milestone_5_invitations = models.PositiveIntegerField(default=30, help_text="Free days for 5 successful invitations")
    milestone_10_invitations = models.PositiveIntegerField(default=60, help_text="Free days for 10 successful invitations")
    milestone_20_invitations = models.PositiveIntegerField(default=120, help_text="Free days for 20 successful invitations")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Referral Program"
        verbose_name_plural = "Referral Programs"
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

class UserReferralStats(models.Model):
    """User referral statistics"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Invitation counts
    invitations_sent = models.PositiveIntegerField(default=0, help_text="Total invitations sent")
    invitations_used = models.PositiveIntegerField(default=0, help_text="Total invitations used")
    invitations_expired = models.PositiveIntegerField(default=0, help_text="Total invitations expired")
    
    # Reward tracking
    total_rewards_earned = models.PositiveIntegerField(default=0, help_text="Total free days earned")
    total_rewards_used = models.PositiveIntegerField(default=0, help_text="Total free days used")
    
    # Milestone tracking
    milestone_5_reached = models.BooleanField(default=False)
    milestone_10_reached = models.BooleanField(default=False)
    milestone_20_reached = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Referral Statistics"
        verbose_name_plural = "User Referral Statistics"
    
    def __str__(self):
        return f"{self.user.username} - {self.invitations_used} successful referrals"
    
    @property
    def conversion_rate(self):
        """Calculate invitation conversion rate"""
        if self.invitations_sent == 0:
            return 0
        return (self.invitations_used / self.invitations_sent) * 100
    
    @property
    def available_rewards(self):
        """Get available rewards"""
        return self.total_rewards_earned - self.total_rewards_used

class JobDescription(models.Model):
    """Job Description model for storing external job postings"""
    
    SOURCE_CHOICES = (
        ('manual', 'Manual Input'),
        ('api', 'External API'),
        ('crawler', 'Crawler Project'),
        ('upload', 'File Upload'),
    )
    
    JOB_TYPE_CHOICES = (
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    )
    
    # Basic information
    title = models.CharField(max_length=200, help_text="Job title")
    company = models.CharField(max_length=200, help_text="Company name")
    location = models.CharField(max_length=200, help_text="Job location")
    description = models.TextField(help_text="Full job description")
    
    # Requirements
    required_skills = models.JSONField(default=list, help_text="Required skills")
    preferred_skills = models.JSONField(default=list, help_text="Preferred skills")
    experience_level = models.CharField(max_length=50, help_text="Experience requirement")
    education_level = models.CharField(max_length=50, help_text="Education requirement")
    salary_range = models.CharField(max_length=100, blank=True, help_text="Salary range")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full-time')
    
    # External API integration
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    source_url = models.URLField(blank=True, help_text="Original job posting URL")
    external_id = models.CharField(max_length=100, blank=True, help_text="External system ID")
    api_source = models.CharField(max_length=50, blank=True, help_text="API source name")
    
    # Processing status
    is_processed = models.BooleanField(default=False, help_text="Whether JD has been processed for matching")
    processing_errors = models.TextField(blank=True, help_text="Any errors during processing")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'company']),
            models.Index(fields=['source', 'is_processed']),
            models.Index(fields=['external_id', 'api_source']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def total_skills(self):
        """Get total number of skills"""
        return len(self.required_skills) + len(self.preferred_skills)
    
    @property
    def skill_density(self):
        """Calculate skill density in description"""
        if not self.description:
            return 0
        total_skills = self.total_skills
        description_length = len(self.description.split())
        return total_skills / description_length if description_length > 0 else 0

class ResumeJobMatch(models.Model):
    """Model for storing resume-job matching results"""
    
    resume = models.ForeignKey('Resume', on_delete=models.CASCADE, related_name='job_matches')
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name='resume_matches')
    
    # Match scores
    overall_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Overall match score (0-100)")
    skill_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Skill match score")
    experience_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Experience match score")
    education_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Education match score")
    
    # Match details
    matched_skills = models.JSONField(default=list, help_text="Skills that match")
    missing_skills = models.JSONField(default=list, help_text="Skills that are missing")
    skill_gaps = models.JSONField(default=list, help_text="Detailed skill gaps")
    
    # Match metadata
    match_level = models.CharField(max_length=20, help_text="Match level: excellent, good, fair, poor")
    match_recommendations = models.JSONField(default=list, help_text="Recommendations for improvement")
    
    # User feedback for AI learning
    user_feedback = models.TextField(blank=True, help_text="User feedback on match accuracy")
    feedback_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True, help_text="User rating (1-5)"
    )
    feedback_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-overall_match_score']
        unique_together = ['resume', 'job_description']
        indexes = [
            models.Index(fields=['overall_match_score']),
            models.Index(fields=['match_level']),
            models.Index(fields=['feedback_rating']),
        ]
    
    def __str__(self):
        return f"{self.resume.title} - {self.job_description.title} ({self.overall_match_score}%)"
    
    @property
    def is_excellent_match(self):
        return self.overall_match_score >= 90
    
    @property
    def is_good_match(self):
        return 80 <= self.overall_match_score < 90
    
    @property
    def is_fair_match(self):
        return 70 <= self.overall_match_score < 80
    
    @property
    def is_poor_match(self):
        return self.overall_match_score < 70

class KeywordMatch(models.Model):
    """Model for free tier keyword matching"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey('Resume', on_delete=models.CASCADE, related_name='keyword_matches')
    
    # Keywords provided by user
    target_keywords = models.JSONField(default=list, help_text="Keywords user wants to match")
    target_job_title = models.CharField(max_length=200, blank=True, help_text="Target job title")
    target_industry = models.CharField(max_length=100, blank=True, help_text="Target industry")
    
    # Match results
    keyword_match_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Keyword match score")
    matched_keywords = models.JSONField(default=list, help_text="Keywords that match")
    missing_keywords = models.JSONField(default=list, help_text="Keywords that are missing")
    
    # Basic recommendations
    basic_recommendations = models.JSONField(default=list, help_text="Basic improvement recommendations")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-keyword_match_score']
    
    def __str__(self):
        return f"{self.user.username} - {self.target_job_title} ({self.keyword_match_score}%)"

# ExternalAPIConfig model removed - replaced by ExternalServiceIntegration

class Resume(models.Model):
    """Resume model for storing user resumes"""
    
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('failed', 'Analysis Failed'),
    )
    
    # Basic information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, help_text="Resume title/name")
    file = models.FileField(upload_to='resumes/', help_text="Resume PDF file")
    
    # Analysis status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    
    # File information
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, default='pdf', help_text="File type")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def is_analyzed(self):
        return self.status == 'analyzed'
    
    @property
    def has_analysis(self):
        return hasattr(self, 'analysis') and self.analysis is not None

class ResumeAnalysis(models.Model):
    """AI analysis results for resumes"""
    
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='analysis')
    
    # Overall scores
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Overall resume score (0-100)")
    structure_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Structure and format score")
    content_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Content quality score")
    keyword_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Keyword optimization score")
    ats_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="ATS compatibility score")
    
    # Analysis details
    extracted_text = models.TextField(help_text="Extracted text from resume")
    detected_keywords = models.JSONField(default=list, help_text="Detected keywords")
    missing_keywords = models.JSONField(default=list, help_text="Missing important keywords")
    industry_keywords = models.JSONField(default=list, help_text="Industry-specific keywords found")
    
    # Skills analysis
    technical_skills = models.JSONField(default=list, help_text="Technical skills identified")
    soft_skills = models.JSONField(default=list, help_text="Soft skills identified")
    skill_gaps = models.JSONField(default=list, help_text="Recommended skills to add")
    
    # Experience analysis
    experience_years = models.PositiveIntegerField(default=0, help_text="Years of experience detected")
    job_titles = models.JSONField(default=list, help_text="Job titles found")
    companies = models.JSONField(default=list, help_text="Companies mentioned")
    
    # Education analysis
    education_level = models.CharField(max_length=100, blank=True, help_text="Highest education level")
    institutions = models.JSONField(default=list, help_text="Educational institutions")
    certifications = models.JSONField(default=list, help_text="Certifications found")
    
    # AI analysis metadata
    analysis_version = models.CharField(max_length=20, default='1.0', help_text="AI analysis version")
    processing_time = models.DecimalField(max_digits=5, decimal_places=2, help_text="Analysis processing time in seconds")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="AI confidence in analysis")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis for {self.resume.title}"
    
    @property
    def score_category(self):
        """Get score category based on overall score"""
        if self.overall_score >= 90:
            return 'excellent'
        elif self.overall_score >= 80:
            return 'good'
        elif self.overall_score >= 70:
            return 'fair'
        elif self.overall_score >= 60:
            return 'needs_improvement'
        else:
            return 'poor'

class ResumeFeedback(models.Model):
    """Detailed feedback and recommendations for resumes"""
    
    analysis = models.OneToOneField(ResumeAnalysis, on_delete=models.CASCADE, related_name='feedback')
    
    # General feedback
    summary = models.TextField(help_text="Overall resume summary")
    strengths = models.JSONField(default=list, help_text="Resume strengths")
    weaknesses = models.JSONField(default=list, help_text="Areas for improvement")
    
    # Specific recommendations
    structure_recommendations = models.JSONField(default=list, help_text="Structure improvement suggestions")
    content_recommendations = models.JSONField(default=list, help_text="Content improvement suggestions")
    keyword_recommendations = models.JSONField(default=list, help_text="Keyword optimization suggestions")
    format_recommendations = models.JSONField(default=list, help_text="Formatting suggestions")
    
    # Industry-specific advice
    industry_insights = models.JSONField(default=list, help_text="Industry-specific insights")
    market_trends = models.JSONField(default=list, help_text="Current market trends")
    salary_insights = models.JSONField(default=dict, help_text="Salary and compensation insights")
    
    # Action items
    priority_actions = models.JSONField(default=list, help_text="High priority actions to take")
    quick_fixes = models.JSONField(default=list, help_text="Quick fixes that can be done immediately")
    long_term_improvements = models.JSONField(default=list, help_text="Long-term improvement suggestions")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback for {self.analysis.resume.title}"

class ResumeComparison(models.Model):
    """Enhanced resume comparison model"""
    
    COMPARISON_TYPE_CHOICES = (
        ('version', 'Version Comparison'),
        ('template', 'Template Comparison'),
        ('before_after', 'Before/After Analysis'),
        ('multi_resume', 'Multiple Resume Comparison'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resume_comparisons')
    title = models.CharField(max_length=200, help_text="Comparison title")
    description = models.TextField(blank=True, help_text="Comparison description")
    comparison_type = models.CharField(max_length=20, choices=COMPARISON_TYPE_CHOICES, default='version')
    
    # Resumes being compared (supporting multiple resumes)
    resumes = models.ManyToManyField(Resume, through='ResumeComparisonItem', related_name='comparisons')
    
    # Comparison metrics
    overall_improvement = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Overall improvement percentage")
    score_changes = models.JSONField(default=dict, help_text="Detailed score changes by category")
    improvement_areas = models.JSONField(default=list, help_text="Areas of improvement")
    maintained_strengths = models.JSONField(default=list, help_text="Strengths that were maintained")
    new_weaknesses = models.JSONField(default=list, help_text="New areas of concern")
    
    # Comparison metadata
    comparison_date = models.DateTimeField(default=timezone.now)
    analysis_notes = models.TextField(blank=True, help_text="Additional analysis notes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ResumeComparisonItem(models.Model):
    """Individual resume in a comparison"""
    
    comparison = models.ForeignKey(ResumeComparison, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Order in comparison")
    label = models.CharField(max_length=100, blank=True, help_text="Label for this resume in comparison")
    
    # Individual scores for this resume
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    structure_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    content_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    keyword_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ats_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['comparison', 'resume']
        ordering = ['order']
    
    def __str__(self):
        return f"{self.comparison.title} - {self.resume.title}"

class ResumeTemplate(models.Model):
    """Resume templates for different industries and roles"""
    
    TEMPLATE_TYPE_CHOICES = (
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('creative', 'Creative'),
        ('minimal', 'Minimal'),
        ('professional', 'Professional'),
    )
    
    INDUSTRY_CHOICES = (
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('marketing', 'Marketing'),
        ('education', 'Education'),
        ('general', 'General'),
    )
    
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(help_text="Template description")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES, default='general')
    
    # Template files
    html_template = models.TextField(help_text="HTML template content")
    css_styles = models.TextField(help_text="CSS styles for template")
    
    # Template metadata
    is_active = models.BooleanField(default=True, help_text="Whether template is available for use")
    is_premium = models.BooleanField(default=False, help_text="Whether template requires premium subscription")
    usage_count = models.PositiveIntegerField(default=0, help_text="Number of times template has been used")
    
    # Preview image
    preview_image = models.ImageField(upload_to='resume_templates/', blank=True, help_text="Template preview image")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_industry_display()}"

class ResumeExport(models.Model):
    """Model for tracking resume exports and downloads"""
    
    EXPORT_FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Plain Text'),
        ('html', 'HTML'),
    )
    
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='exports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resume_exports')
    
    # Export details
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMAT_CHOICES)
    file_path = models.CharField(max_length=500, help_text="Path to exported file")
    file_size = models.PositiveIntegerField(help_text="Exported file size in bytes")
    
    # Export metadata
    template_used = models.ForeignKey(ResumeTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    customizations = models.JSONField(default=dict, help_text="Customizations applied during export")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.resume.title} - {self.export_format} export"

class UserDataConsent(models.Model):
    """User data consent and privacy settings"""
    
    CONSENT_TYPE_CHOICES = (
        ('data_collection', 'Data Collection'),
        ('data_processing', 'Data Processing'),
        ('data_sharing', 'Data Sharing'),
        ('marketing', 'Marketing Communications'),
        ('third_party', 'Third Party Services'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_consents')
    consent_type = models.CharField(max_length=20, choices=CONSENT_TYPE_CHOICES)
    is_granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    consent_version = models.CharField(max_length=10, default='1.0')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'consent_type']
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.consent_type}"

class DataRetentionPolicy(models.Model):
    """Data retention policy configuration"""
    
    DATA_TYPE_CHOICES = (
        ('resume_files', 'Resume Files'),
        ('analysis_results', 'Analysis Results'),
        ('match_results', 'Match Results'),
        ('user_activity', 'User Activity Logs'),
        ('personal_info', 'Personal Information'),
    )
    
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, unique=True)
    retention_period_days = models.PositiveIntegerField(help_text="Days to retain data")
    auto_delete = models.BooleanField(default=True, help_text="Automatically delete after retention period")
    anonymize_before_delete = models.BooleanField(default=False, help_text="Anonymize data before deletion")
    legal_hold = models.BooleanField(default=False, help_text="Legal hold - do not delete")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Data Retention Policy"
        verbose_name_plural = "Data Retention Policies"
    
    def __str__(self):
        return f"{self.data_type} - {self.retention_period_days} days"

class UserDataDeletionRequest(models.Model):
    """User data deletion requests"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deletion_requests')
    request_type = models.CharField(max_length=20, choices=DataRetentionPolicy.DATA_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # Verification
    verification_email_sent = models.BooleanField(default=False)
    verification_email_sent_at = models.DateTimeField(null=True, blank=True)
    verification_completed = models.BooleanField(default=False)
    verification_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.request_type} - {self.status}"

class LegalDisclaimer(models.Model):
    """Legal disclaimers and terms"""
    
    DISCLAIMER_TYPE_CHOICES = (
        ('resume_analysis', 'Resume Analysis Disclaimer'),
        ('job_matching', 'Job Matching Disclaimer'),
        ('data_processing', 'Data Processing Disclaimer'),
        ('ai_limitations', 'AI Limitations Disclaimer'),
        ('privacy_policy', 'Privacy Policy'),
        ('terms_of_service', 'Terms of Service'),
    )
    
    disclaimer_type = models.CharField(max_length=20, choices=DISCLAIMER_TYPE_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    version = models.CharField(max_length=10, default='1.0')
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    requires_consent = models.BooleanField(default=False, help_text="Whether user must consent to this disclaimer")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.disclaimer_type} v{self.version}"

class UserDisclaimerConsent(models.Model):
    """User consent to legal disclaimers"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disclaimer_consents')
    disclaimer = models.ForeignKey(LegalDisclaimer, on_delete=models.CASCADE)
    consented_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'disclaimer']
        ordering = ['-consented_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.disclaimer.disclaimer_type}"

class ExternalServiceIntegration(models.Model):
    """External service integration configuration"""
    
    SERVICE_TYPE_CHOICES = (
        ('job_crawler', 'Job Crawler Service'),
        ('resume_matcher', 'Resume Matcher Service'),
        ('ai_analyzer', 'AI Analysis Service'),
        ('ats_integration', 'ATS Integration'),
    )
    
    name = models.CharField(max_length=100, help_text="Service name")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    base_url = models.URLField(help_text="Service base URL")
    api_key = models.CharField(max_length=255, blank=True, help_text="API key if required")
    
    # Configuration
    is_active = models.BooleanField(default=True, help_text="Whether this service is active")
    rate_limit = models.PositiveIntegerField(default=100, help_text="Requests per minute")
    timeout = models.PositiveIntegerField(default=30, help_text="Request timeout in seconds")
    
    # Authentication
    auth_type = models.CharField(max_length=20, default='none', help_text="Authentication type")
    auth_headers = models.JSONField(default=dict, help_text="Authentication headers")
    
    # Legal compliance
    data_processing_agreement = models.BooleanField(default=False, help_text="Has data processing agreement")
    privacy_policy_url = models.URLField(blank=True, help_text="Service privacy policy URL")
    terms_of_service_url = models.URLField(blank=True, help_text="Service terms of service URL")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "External Service Integration"
        verbose_name_plural = "External Service Integrations"
    
    def __str__(self):
        return f"{self.name} ({self.service_type})"

class ServiceUsageLog(models.Model):
    """Log of external service usage"""
    
    service = models.ForeignKey(ExternalServiceIntegration, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    # Request details
    endpoint = models.CharField(max_length=200, help_text="API endpoint called")
    request_method = models.CharField(max_length=10, help_text="HTTP method")
    request_data = models.JSONField(default=dict, help_text="Request data sent")
    response_status = models.PositiveIntegerField(help_text="HTTP response status")
    response_data = models.JSONField(default=dict, help_text="Response data received")
    
    # Performance metrics
    request_time = models.DecimalField(max_digits=5, decimal_places=2, help_text="Request time in seconds")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Error tracking
    error_message = models.TextField(blank=True, help_text="Error message if any")
    is_success = models.BooleanField(default=True, help_text="Whether request was successful")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['service', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.service.name} - {self.endpoint} - {self.timestamp}"
