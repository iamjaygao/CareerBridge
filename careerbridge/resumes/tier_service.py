from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import UserSubscription, KeywordMatch, ResumeJobMatch, JobDescription
from .services import ResumeAnalysisService

class TierService:
    """Service class for handling tier-based functionality"""
    
    def __init__(self, user):
        self.user = user
        self.subscription = self._get_or_create_subscription()
    
    def _get_or_create_subscription(self):
        """Get or create user subscription"""
        subscription, created = UserSubscription.objects.get_or_create(
            user=self.user,
            defaults={'tier': 'free'}
        )
        return subscription
    
    def _check_monthly_reset(self):
        """Check and reset monthly usage if needed"""
        current_date = timezone.now().date()
        if current_date.month != self.subscription.last_reset_date.month or current_date.year != self.subscription.last_reset_date.year:
            # Reset monthly usage
            self.subscription.current_month_uploads = 0
            self.subscription.current_month_analyses = 0
            self.subscription.current_month_matches = 0
            self.subscription.last_reset_date = current_date
            self.subscription.save()
    
    def can_upload_resume(self):
        """Check if user can upload resume"""
        self._check_monthly_reset()
        return self.subscription.can_upload_resume()
    
    def can_analyze_resume(self):
        """Check if user can analyze resume"""
        self._check_monthly_reset()
        return self.subscription.can_analyze_resume()
    
    def can_match_jd(self):
        """Check if user can match JD"""
        self._check_monthly_reset()
        return self.subscription.can_match_jd()
    
    def increment_upload_count(self):
        """Increment upload count"""
        self.subscription.increment_upload_count()
    
    def increment_analysis_count(self):
        """Increment analysis count"""
        self.subscription.increment_analysis_count()
    
    def increment_match_count(self):
        """Increment match count"""
        self.subscription.increment_match_count()
    
    def get_usage_stats(self):
        """Get current usage statistics"""
        self._check_monthly_reset()
        
        return {
            'tier': self.subscription.tier,
            'uploads_used': self.subscription.current_month_uploads,
            'uploads_limit': self.subscription.monthly_resume_uploads,
            'analyses_used': self.subscription.current_month_analyses,
            'analyses_limit': self.subscription.monthly_analyses,
            'matches_used': self.subscription.current_month_matches,
            'matches_limit': self.subscription.monthly_jd_matches,
        }

class FreeTierService:
    """Service for free tier functionality"""
    
    def __init__(self, user):
        self.user = user
        self.tier_service = TierService(user)
    
    def analyze_resume_with_keywords(self, resume_id, keywords, job_title=None, industry=None):
        """Analyze resume with user-provided keywords (free tier)"""
        
        if not self.tier_service.can_analyze_resume():
            raise PermissionDenied("Monthly analysis limit reached. Upgrade to Premium for unlimited analyses.")
        
        # Get resume
        from .models import Resume
        try:
            resume = Resume.objects.get(id=resume_id, user=self.user)
        except Resume.DoesNotExist:
            raise ValueError("Resume not found")
        
        # Perform basic analysis
        analysis_service = ResumeAnalysisService()
        analysis_result = analysis_service.analyze_resume(resume)
        
        # Create keyword match
        keyword_match = KeywordMatch.objects.create(
            user=self.user,
            resume=resume,
            target_keywords=keywords,
            target_job_title=job_title or '',
            target_industry=industry or '',
            keyword_match_score=self._calculate_keyword_match(analysis_result, keywords),
            matched_keywords=self._get_matched_keywords(analysis_result, keywords),
            missing_keywords=self._get_missing_keywords(analysis_result, keywords),
            basic_recommendations=self._generate_basic_recommendations(analysis_result, keywords)
        )
        
        # Increment usage
        self.tier_service.increment_analysis_count()
        
        return keyword_match
    
    def _calculate_keyword_match(self, analysis_result, keywords):
        """Calculate keyword match score"""
        if not keywords:
            return Decimal('0.00')
        
        # Get all skills from analysis
        all_skills = set()
        if 'technical_skills' in analysis_result:
            all_skills.update(analysis_result['technical_skills'])
        if 'soft_skills' in analysis_result:
            all_skills.update(analysis_result['soft_skills'])
        
        # Calculate match
        matched_count = 0
        for keyword in keywords:
            if keyword.lower() in [skill.lower() for skill in all_skills]:
                matched_count += 1
        
        return Decimal(str(round((matched_count / len(keywords)) * 100, 2)))
    
    def _get_matched_keywords(self, analysis_result, keywords):
        """Get matched keywords"""
        all_skills = set()
        if 'technical_skills' in analysis_result:
            all_skills.update(analysis_result['technical_skills'])
        if 'soft_skills' in analysis_result:
            all_skills.update(analysis_result['soft_skills'])
        
        matched = []
        for keyword in keywords:
            if keyword.lower() in [skill.lower() for skill in all_skills]:
                matched.append(keyword)
        
        return matched
    
    def _get_missing_keywords(self, analysis_result, keywords):
        """Get missing keywords"""
        all_skills = set()
        if 'technical_skills' in analysis_result:
            all_skills.update(analysis_result['technical_skills'])
        if 'soft_skills' in analysis_result:
            all_skills.update(analysis_result['soft_skills'])
        
        missing = []
        for keyword in keywords:
            if keyword.lower() not in [skill.lower() for skill in all_skills]:
                missing.append(keyword)
        
        return missing
    
    def _generate_basic_recommendations(self, analysis_result, keywords):
        """Generate basic recommendations for free tier"""
        recommendations = []
        
        # Check for missing keywords
        missing_keywords = self._get_missing_keywords(analysis_result, keywords)
        if missing_keywords:
            recommendations.append({
                'type': 'keyword',
                'priority': 'high',
                'message': f"Add these keywords to your resume: {', '.join(missing_keywords)}"
            })
        
        # Check overall score
        if 'overall_score' in analysis_result:
            score = analysis_result['overall_score']
            if score < 70:
                recommendations.append({
                    'type': 'general',
                    'priority': 'medium',
                    'message': "Your resume needs improvement. Consider upgrading to Premium for detailed analysis."
                })
        
        return recommendations

class PremiumTierService:
    """Service for premium tier functionality"""
    
    def __init__(self, user):
        self.user = user
        self.tier_service = TierService(user)
    
    def analyze_resume_with_jd(self, resume_id, jd_text, job_title, company, location):
        """Analyze resume with specific job description (premium tier)"""
        
        if not self.tier_service.can_analyze_resume():
            raise PermissionDenied("Monthly analysis limit reached.")
        
        # Get resume
        from .models import Resume
        try:
            resume = Resume.objects.get(id=resume_id, user=self.user)
        except Resume.DoesNotExist:
            raise ValueError("Resume not found")
        
        # Create job description
        # JDProcessor functionality moved to external service
        processor = JDProcessor()
        job_description = processor.process_jd(jd_text, job_title, company, location)
        
        # Perform detailed analysis - moved to external service
        # from .jd_matcher import JDMatcher
        # matcher = JDMatcher()
        # match_result = matcher.match_resume_to_jd(resume.id, job_description.id)
        
        # Increment usage
        self.tier_service.increment_analysis_count()
        self.tier_service.increment_match_count()
        
        return match_result
    
    def provide_feedback(self, match_id, feedback_text, rating):
        """Provide feedback on match accuracy (premium tier)"""
        
        try:
            match = ResumeJobMatch.objects.get(id=match_id)
            # Ensure user owns the resume
            if match.resume.user != self.user:
                raise PermissionDenied("You can only provide feedback on your own matches.")
            
            # Update feedback
            match.user_feedback = feedback_text
            match.feedback_rating = rating
            match.feedback_date = timezone.now()
            match.save()
            
            return match
            
        except ResumeJobMatch.DoesNotExist:
            raise ValueError("Match not found")

class EnterpriseTierService:
    """Service for enterprise tier functionality"""
    
    def __init__(self, user):
        self.user = user
        self.tier_service = TierService(user)
    
    def batch_analyze_resumes(self, resume_ids, jd_ids):
        """Batch analyze multiple resumes against multiple JDs (enterprise tier)"""
        
        results = []
        for resume_id in resume_ids:
            for jd_id in jd_ids:
                try:
                    # from .jd_matcher import JDMatcher
                    # matcher = JDMatcher()
                    # match = matcher.match_resume_to_jd(resume_id, jd_id)
                    # results.append(match)
                    # Moved to external service
                    pass
                except Exception as e:
                    results.append({'error': str(e), 'resume_id': resume_id, 'jd_id': jd_id})
        
        return results
    
    def integrate_external_api(self, api_config):
        """Integrate with external API (enterprise tier)"""
        
        from .models import ExternalServiceIntegration
        config = ExternalServiceIntegration.objects.create(
            name=api_config['name'],
            api_type=api_config['api_type'],
            base_url=api_config['base_url'],
            api_key=api_config.get('api_key', ''),
            is_active=api_config.get('is_active', True),
            rate_limit=api_config.get('rate_limit', 100),
            timeout=api_config.get('timeout', 30),
            jobs_endpoint=api_config.get('jobs_endpoint', '/jobs'),
            search_endpoint=api_config.get('search_endpoint', '/search'),
            auth_type=api_config.get('auth_type', 'none'),
            auth_headers=api_config.get('auth_headers', {})
        )
        
        return config

class TierFactory:
    """Factory class for creating appropriate tier service"""
    
    @staticmethod
    def get_service(user, tier=None):
        """Get appropriate service based on user tier"""
        
        if tier is None:
            subscription = TierService(user).subscription
            tier = subscription.tier
        
        if tier == 'free':
            return FreeTierService(user)
        elif tier == 'premium':
            return PremiumTierService(user)
        elif tier == 'enterprise':
            return EnterpriseTierService(user)
        else:
            raise ValueError(f"Unknown tier: {tier}")
    
    @staticmethod
    def get_tier_service(user):
        """Get tier service for usage management"""
        return TierService(user) 