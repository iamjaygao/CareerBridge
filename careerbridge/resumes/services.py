import time
import json
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, Avg, Count
from .models import Resume, ResumeAnalysis, ResumeFeedback

class ResumeAnalysisService:
    """Service class for resume analysis operations"""
    
    @staticmethod
    def analyze_resume(resume_id, industry=None, job_title=None):
        """
        Analyze a resume using AI
        This is a mock implementation - in production, integrate with OpenAI API
        """
        try:
            resume = Resume.objects.get(id=resume_id)
            
            # Update status to analyzing
            resume.status = 'analyzing'
            resume.save()
            
            # Simulate AI processing time
            start_time = time.time()
            time.sleep(2)  # Simulate processing
            processing_time = time.time() - start_time
            
            # Mock analysis results
            analysis_data = ResumeAnalysisService._generate_mock_analysis(
                resume, industry, job_title
            )
            
            # Create analysis record
            analysis = ResumeAnalysis.objects.create(
                resume=resume,
                processing_time=Decimal(str(processing_time)),
                **analysis_data
            )
            
            # Create feedback
            feedback_data = ResumeAnalysisService._generate_mock_feedback(analysis)
            ResumeFeedback.objects.create(
                analysis=analysis,
                **feedback_data
            )
            
            # Update resume status
            resume.status = 'analyzed'
            resume.analyzed_at = timezone.now()
            resume.save()
            
            return analysis
            
        except Resume.DoesNotExist:
            raise ValueError("Resume not found")
        except Exception as e:
            # Update resume status to failed
            resume.status = 'failed'
            resume.save()
            raise e
    
    @staticmethod
    def _generate_mock_analysis(resume, industry=None, job_title=None):
        """Generate mock analysis data"""
        # This would be replaced with actual AI analysis
        base_score = 75.0
        
        # Adjust score based on file size (simulating content quality)
        if resume.file_size > 50000:  # Larger file might have more content
            base_score += 5
        
        # Industry-specific adjustments
        if industry == 'technology':
            base_score += 3
        elif industry == 'finance':
            base_score += 2
        
        return {
            'overall_score': Decimal(str(base_score)),
            'structure_score': Decimal(str(base_score - 5)),
            'content_score': Decimal(str(base_score + 2)),
            'keyword_score': Decimal(str(base_score - 3)),
            'ats_score': Decimal(str(base_score - 1)),
            'extracted_text': f"Mock extracted text from {resume.title}",
            'detected_keywords': ['python', 'django', 'react', 'javascript', 'sql'],
            'missing_keywords': ['docker', 'kubernetes', 'aws'],
            'industry_keywords': ['software development', 'web development'],
            'technical_skills': ['Python', 'Django', 'React', 'JavaScript', 'SQL'],
            'soft_skills': ['Leadership', 'Communication', 'Problem Solving'],
            'skill_gaps': ['Docker', 'Kubernetes', 'AWS'],
            'experience_years': 3,
            'job_titles': ['Software Engineer', 'Developer'],
            'companies': ['Tech Corp', 'Startup Inc'],
            'education_level': 'Bachelor\'s Degree',
            'institutions': ['University of Technology'],
            'certifications': ['AWS Certified Developer'],
            'analysis_version': '1.0',
            'confidence_score': Decimal('0.85'),
        }
    
    @staticmethod
    def _generate_mock_feedback(analysis):
        """Generate mock feedback data"""
        return {
            'summary': f"Your resume shows good technical skills but could benefit from more industry-specific keywords and improved structure.",
            'strengths': [
                'Strong technical skills in Python and web development',
                'Good project experience',
                'Clear work history'
            ],
            'weaknesses': [
                'Missing some industry keywords',
                'Could improve structure and formatting',
                'Limited quantifiable achievements'
            ],
            'structure_recommendations': [
                'Add a professional summary at the top',
                'Use bullet points for better readability',
                'Include quantifiable achievements'
            ],
            'content_recommendations': [
                'Add more specific project descriptions',
                'Include metrics and results',
                'Highlight leadership experience'
            ],
            'keyword_recommendations': [
                'Add Docker and Kubernetes to skills',
                'Include AWS or cloud platform experience',
                'Add agile methodology keywords'
            ],
            'format_recommendations': [
                'Use consistent formatting throughout',
                'Ensure proper spacing between sections',
                'Use professional fonts'
            ],
            'industry_insights': [
                'Technology industry values practical experience',
                'Cloud skills are highly in demand',
                'Agile methodology is preferred'
            ],
            'market_trends': [
                'Remote work is becoming standard',
                'DevOps skills are increasingly important',
                'Full-stack development is in high demand'
            ],
            'salary_insights': {
                'entry_level': '$60,000 - $80,000',
                'mid_level': '$80,000 - $120,000',
                'senior_level': '$120,000 - $180,000'
            },
            'priority_actions': [
                'Add missing technical keywords',
                'Improve resume structure',
                'Include quantifiable achievements'
            ],
            'quick_fixes': [
                'Fix formatting inconsistencies',
                'Add missing contact information',
                'Update skills section'
            ],
            'long_term_improvements': [
                'Gain additional certifications',
                'Build more project portfolio',
                'Develop leadership skills'
            ]
        }

class ResumeSearchService:
    """Service class for resume search and filtering"""
    
    @staticmethod
    def search_resumes(user, query=None, status=None, date_from=None, date_to=None):
        """Search resumes with various filters"""
        queryset = Resume.objects.filter(user=user)
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(file__icontains=query)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(uploaded_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(uploaded_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def filter_resumes(user, filters):
        """Filter resumes based on various criteria"""
        queryset = Resume.objects.filter(user=user)
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('file_type'):
            queryset = queryset.filter(file_type=filters['file_type'])
        
        if filters.get('has_analysis') is not None:
            if filters['has_analysis']:
                queryset = queryset.filter(analysis__isnull=False)
            else:
                queryset = queryset.filter(analysis__isnull=True)
        
        if filters.get('date_range'):
            date_range = filters['date_range']
            today = timezone.now().date()
            
            if date_range == 'today':
                queryset = queryset.filter(uploaded_at__date=today)
            elif date_range == 'week':
                week_ago = today - timezone.timedelta(days=7)
                queryset = queryset.filter(uploaded_at__date__gte=week_ago)
            elif date_range == 'month':
                month_ago = today - timezone.timedelta(days=30)
                queryset = queryset.filter(uploaded_at__date__gte=month_ago)
            elif date_range == 'year':
                year_ago = today - timezone.timedelta(days=365)
                queryset = queryset.filter(uploaded_at__date__gte=year_ago)
        
        return queryset.order_by('-created_at')

class ResumeStatsService:
    """Service class for resume statistics"""
    
    @staticmethod
    def get_user_stats(user):
        """Get resume statistics for a user"""
        resumes = Resume.objects.filter(user=user)
        
        total_resumes = resumes.count()
        analyzed_resumes = resumes.filter(status='analyzed').count()
        pending_analysis = resumes.filter(status='uploaded').count()
        
        # Calculate average score
        average_score = resumes.filter(
            analysis__isnull=False
        ).aggregate(
            avg_score=Avg('analysis__overall_score')
        )['avg_score'] or Decimal('0.00')
        
        # Score distribution
        score_distribution = {
            'excellent': resumes.filter(analysis__overall_score__gte=90).count(),
            'good': resumes.filter(analysis__overall_score__gte=80, analysis__overall_score__lt=90).count(),
            'fair': resumes.filter(analysis__overall_score__gte=70, analysis__overall_score__lt=80).count(),
            'needs_improvement': resumes.filter(analysis__overall_score__gte=60, analysis__overall_score__lt=70).count(),
            'poor': resumes.filter(analysis__overall_score__lt=60).count(),
        }
        
        # Recent uploads
        recent_uploads = resumes.order_by('-created_at')[:5]
        
        return {
            'total_resumes': total_resumes,
            'analyzed_resumes': analyzed_resumes,
            'pending_analysis': pending_analysis,
            'average_score': average_score,
            'score_distribution': score_distribution,
            'recent_uploads': recent_uploads,
        }
    
    @staticmethod
    def get_platform_stats():
        """Get platform-wide resume statistics"""
        resumes = Resume.objects.all()
        
        total_resumes = resumes.count()
        analyzed_resumes = resumes.filter(status='analyzed').count()
        pending_analysis = resumes.filter(status='uploaded').count()
        
        average_score = resumes.filter(
            analysis__isnull=False
        ).aggregate(
            avg_score=Avg('analysis__overall_score')
        )['avg_score'] or Decimal('0.00')
        
        # File type distribution
        file_type_distribution = resumes.values('file_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Status distribution
        status_distribution = resumes.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_resumes': total_resumes,
            'analyzed_resumes': analyzed_resumes,
            'pending_analysis': pending_analysis,
            'average_score': average_score,
            'file_type_distribution': list(file_type_distribution),
            'status_distribution': list(status_distribution),
        }

class ResumeComparisonService:
    """Service class for resume comparison operations"""
    
    @staticmethod
    def compare_resumes(original_resume, improved_resume):
        """Compare two resumes and calculate improvement metrics"""
        if not original_resume.has_analysis or not improved_resume.has_analysis:
            raise ValueError("Both resumes must have analysis data")
        
        original_score = original_resume.analysis.overall_score
        improved_score = improved_resume.analysis.overall_score
        
        score_improvement = improved_score - original_score
        
        # Calculate improvement areas
        improvement_areas = []
        if improved_resume.analysis.keyword_score > original_resume.analysis.keyword_score:
            improvement_areas.append('keyword_optimization')
        if improved_resume.analysis.structure_score > original_resume.analysis.structure_score:
            improvement_areas.append('structure_improvement')
        if improved_resume.analysis.content_score > original_resume.analysis.content_score:
            improvement_areas.append('content_enhancement')
        
        # Identify maintained strengths
        maintained_strengths = []
        if original_resume.analysis.technical_skills and improved_resume.analysis.technical_skills:
            maintained_strengths.append('technical_skills')
        if original_resume.analysis.experience_years == improved_resume.analysis.experience_years:
            maintained_strengths.append('experience_level')
        
        return {
            'score_improvement': score_improvement,
            'improvement_areas': improvement_areas,
            'maintained_strengths': maintained_strengths,
        }

class ResumeCacheService:
    """Service class for resume caching operations"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_cached_analysis(resume_id):
        """Get cached analysis results"""
        cache_key = f"resume_analysis_{resume_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_analysis(resume_id, analysis_data):
        """Cache analysis results"""
        cache_key = f"resume_analysis_{resume_id}"
        cache.set(cache_key, analysis_data, ResumeCacheService.CACHE_TIMEOUT)
    
    @staticmethod
    def clear_cached_analysis(resume_id):
        """Clear cached analysis results"""
        cache_key = f"resume_analysis_{resume_id}"
        cache.delete(cache_key)
    
    @staticmethod
    def get_cached_stats(user_id):
        """Get cached user statistics"""
        cache_key = f"user_stats_{user_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def set_cached_stats(user_id, stats_data):
        """Cache user statistics"""
        cache_key = f"user_stats_{user_id}"
        cache.set(cache_key, stats_data, ResumeCacheService.CACHE_TIMEOUT)
    
    @staticmethod
    def clear_cached_stats(user_id):
        """Clear cached user statistics"""
        cache_key = f"user_stats_{user_id}"
        cache.delete(cache_key) 