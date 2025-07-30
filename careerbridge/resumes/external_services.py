import requests
import json
import time
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from .models import (
    ExternalServiceIntegration, ServiceUsageLog, 
    JobDescription, ResumeJobMatch, Resume
)

class ExternalServiceClient:
    """Base client for external service integration"""
    
    def __init__(self, service_type: str):
        self.service_type = service_type
        self.service_config = self._get_service_config()
    
    def _get_service_config(self) -> Optional[ExternalServiceIntegration]:
        """Get service configuration"""
        try:
            return ExternalServiceIntegration.objects.get(
                service_type=self.service_type,
                is_active=True
            )
        except ExternalServiceIntegration.DoesNotExist:
            return None
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = 'GET', 
        data: Dict = None, 
        user = None
    ) -> Dict:
        """Make HTTP request to external service"""
        if not self.service_config:
            raise ValueError(f"No active configuration found for {self.service_type}")
        
        url = f"{self.service_config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CareerBridge/1.0'
        }
        
        # Add authentication headers
        if self.service_config.auth_headers:
            headers.update(self.service_config.auth_headers)
        
        # Add API key if required
        if self.service_config.api_key:
            headers['Authorization'] = f'Bearer {self.service_config.api_key}'
        
        # Prepare request data
        request_data = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': self.service_config.timeout
        }
        
        if data:
            request_data['json'] = data
        
        # Make request
        start_time = time.time()
        try:
            response = requests.request(**request_data)
            request_time = time.time() - start_time
            
            # Log the request
            self._log_request(
                endpoint=endpoint,
                method=method,
                request_data=data or {},
                response_status=response.status_code,
                response_data=response.json() if response.content else {},
                request_time=request_time,
                is_success=response.status_code < 400,
                user=user
            )
            
            if response.status_code >= 400:
                raise requests.exceptions.RequestException(
                    f"Service returned {response.status_code}: {response.text}"
                )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            request_time = time.time() - start_time
            self._log_request(
                endpoint=endpoint,
                method=method,
                request_data=data or {},
                response_status=0,
                response_data={},
                request_time=request_time,
                is_success=False,
                error_message=str(e),
                user=user
            )
            raise
    
    def _log_request(
        self, 
        endpoint: str, 
        method: str, 
        request_data: Dict, 
        response_status: int,
        response_data: Dict, 
        request_time: float, 
        is_success: bool,
        user = None,
        error_message: str = ""
    ):
        """Log service request"""
        ServiceUsageLog.objects.create(
            service=self.service_config,
            user=user,
            endpoint=endpoint,
            request_method=method,
            request_data=request_data,
            response_status=response_status,
            response_data=response_data,
            request_time=request_time,
            is_success=is_success,
            error_message=error_message
        )

class JobCrawlerServiceClient(ExternalServiceClient):
    """Client for job crawler service"""
    
    def __init__(self):
        super().__init__('job_crawler')
    
    def crawl_jobs(
        self, 
        job_title: str, 
        location: str, 
        sources: List[str] = None,
        limit: int = 20,
        user = None
    ) -> List[Dict]:
        """Crawl jobs from external sources"""
        data = {
            'job_title': job_title,
            'location': location,
            'sources': sources or ['indeed', 'linkedin'],
            'limit': limit
        }
        
        response = self._make_request('crawl', method='POST', data=data, user=user)
        return response.get('jobs', [])
    
    def get_job_details(self, job_id: str, user = None) -> Dict:
        """Get detailed job information"""
        response = self._make_request(f'jobs/{job_id}', user=user)
        return response
    
    def search_jobs(
        self, 
        query: str, 
        filters: Dict = None,
        page: int = 1,
        user = None
    ) -> Dict:
        """Search jobs with filters"""
        data = {
            'query': query,
            'filters': filters or {},
            'page': page
        }
        
        response = self._make_request('search', method='POST', data=data, user=user)
        return response

class ResumeMatcherServiceClient(ExternalServiceClient):
    """Client for resume matching service"""
    
    def __init__(self):
        super().__init__('resume_matcher')
    
    def match_resume_to_jd(
        self, 
        resume_text: str, 
        job_description: str,
        job_title: str = None,
        company: str = None,
        user = None
    ) -> Dict:
        """Match resume to job description"""
        data = {
            'resume_text': resume_text,
            'job_description': job_description,
            'job_title': job_title,
            'company': company
        }
        
        response = self._make_request('match', method='POST', data=data, user=user)
        return response
    
    def batch_match_resumes(
        self, 
        resumes: List[Dict], 
        job_descriptions: List[Dict],
        user = None
    ) -> List[Dict]:
        """Batch match multiple resumes to job descriptions"""
        data = {
            'resumes': resumes,
            'job_descriptions': job_descriptions
        }
        
        response = self._make_request('batch-match', method='POST', data=data, user=user)
        return response.get('matches', [])
    
    def get_match_analysis(
        self, 
        match_id: str,
        user = None
    ) -> Dict:
        """Get detailed match analysis"""
        response = self._make_request(f'matches/{match_id}/analysis', user=user)
        return response
    
    def provide_feedback(
        self, 
        match_id: str, 
        feedback: str, 
        rating: int,
        user = None
    ) -> Dict:
        """Provide feedback on match accuracy"""
        data = {
            'feedback': feedback,
            'rating': rating
        }
        
        response = self._make_request(
            f'matches/{match_id}/feedback', 
            method='POST', 
            data=data, 
            user=user
        )
        return response

class AIAnalysisServiceClient(ExternalServiceClient):
    """Client for AI analysis service"""
    
    def __init__(self):
        super().__init__('ai_analyzer')
    
    def analyze_resume(
        self, 
        resume_text: str,
        industry: str = None,
        job_title: str = None,
        user = None
    ) -> Dict:
        """Analyze resume using AI"""
        data = {
            'resume_text': resume_text,
            'industry': industry,
            'job_title': job_title
        }
        
        response = self._make_request('analyze', method='POST', data=data, user=user)
        return response
    
    def get_analysis_feedback(
        self, 
        analysis_id: str,
        user = None
    ) -> Dict:
        """Get detailed feedback for analysis"""
        response = self._make_request(f'analysis/{analysis_id}/feedback', user=user)
        return response
    
    def compare_resumes(
        self, 
        resume1_text: str, 
        resume2_text: str,
        comparison_type: str = 'version',
        user = None
    ) -> Dict:
        """Compare two resumes"""
        data = {
            'resume1_text': resume1_text,
            'resume2_text': resume2_text,
            'comparison_type': comparison_type
        }
        
        response = self._make_request('compare', method='POST', data=data, user=user)
        return response

class ExternalServiceManager:
    """Manager for external service operations"""
    
    def __init__(self):
        self.job_crawler = JobCrawlerServiceClient()
        self.resume_matcher = ResumeMatcherServiceClient()
        self.ai_analyzer = AIAnalysisServiceClient()
    
    def crawl_and_store_jobs(
        self, 
        job_title: str, 
        location: str, 
        sources: List[str] = None,
        limit: int = 20,
        user = None
    ) -> List[JobDescription]:
        """Crawl jobs and store them in database"""
        try:
            # Crawl jobs from external service
            jobs_data = self.job_crawler.crawl_jobs(
                job_title=job_title,
                location=location,
                sources=sources,
                limit=limit,
                user=user
            )
            
            # Store jobs in database
            stored_jobs = []
            for job_data in jobs_data:
                job, created = JobDescription.objects.get_or_create(
                    external_id=job_data.get('id'),
                    defaults={
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company', ''),
                        'location': job_data.get('location', ''),
                        'description': job_data.get('description', ''),
                        'required_skills': job_data.get('required_skills', []),
                        'preferred_skills': job_data.get('preferred_skills', []),
                        'experience_level': job_data.get('experience_level', ''),
                        'education_level': job_data.get('education_level', ''),
                        'salary_range': job_data.get('salary_range', ''),
                        'job_type': job_data.get('job_type', 'full-time'),
                        'source': 'crawler',
                        'source_url': job_data.get('url', ''),
                        'api_source': 'external_crawler',
                        'is_processed': True
                    }
                )
                stored_jobs.append(job)
            
            return stored_jobs
            
        except Exception as e:
            # Log error and return empty list
            print(f"Error crawling jobs: {e}")
            return []
    
    def match_resume_to_external_jd(
        self, 
        resume: Resume, 
        job_description: JobDescription,
        user = None
    ) -> Optional[ResumeJobMatch]:
        """Match resume to job description using external service"""
        try:
            # Get resume analysis text
            if not resume.has_analysis:
                raise ValueError("Resume must be analyzed before matching")
            
            resume_text = resume.analysis.extracted_text
            
            # Match using external service
            match_result = self.resume_matcher.match_resume_to_jd(
                resume_text=resume_text,
                job_description=job_description.description,
                job_title=job_description.title,
                company=job_description.company,
                user=user
            )
            
            # Create or update match record
            match, created = ResumeJobMatch.objects.get_or_create(
                resume=resume,
                job_description=job_description,
                defaults={
                    'overall_match_score': match_result.get('overall_score', 0),
                    'skill_match_score': match_result.get('skill_score', 0),
                    'experience_match_score': match_result.get('experience_score', 0),
                    'education_match_score': match_result.get('education_score', 0),
                    'matched_skills': match_result.get('matched_skills', []),
                    'missing_skills': match_result.get('missing_skills', []),
                    'skill_gaps': match_result.get('skill_gaps', []),
                    'match_level': match_result.get('match_level', 'fair'),
                    'match_recommendations': match_result.get('recommendations', [])
                }
            )
            
            return match
            
        except Exception as e:
            print(f"Error matching resume to JD: {e}")
            return None
    
    def analyze_resume_externally(
        self, 
        resume: Resume,
        industry: str = None,
        job_title: str = None,
        user = None
    ):
        """Analyze resume using external AI service"""
        try:
            # This would require extracting text from PDF
            # For now, we'll use a placeholder
            resume_text = f"Resume content for {resume.title}"
            
            # Analyze using external service
            analysis_result = self.ai_analyzer.analyze_resume(
                resume_text=resume_text,
                industry=industry,
                job_title=job_title,
                user=user
            )
            
            # Update resume analysis
            if resume.has_analysis:
                analysis = resume.analysis
            else:
                from .models import ResumeAnalysis
                analysis = ResumeAnalysis(resume=resume)
            
            # Update analysis with external results
            analysis.overall_score = analysis_result.get('overall_score', 0)
            analysis.structure_score = analysis_result.get('structure_score', 0)
            analysis.content_score = analysis_result.get('content_score', 0)
            analysis.keyword_score = analysis_result.get('keyword_score', 0)
            analysis.ats_score = analysis_result.get('ats_score', 0)
            analysis.extracted_text = analysis_result.get('extracted_text', '')
            analysis.detected_keywords = analysis_result.get('detected_keywords', [])
            analysis.missing_keywords = analysis_result.get('missing_keywords', [])
            analysis.technical_skills = analysis_result.get('technical_skills', [])
            analysis.soft_skills = analysis_result.get('soft_skills', [])
            analysis.skill_gaps = analysis_result.get('skill_gaps', [])
            analysis.confidence_score = analysis_result.get('confidence_score', 0)
            
            analysis.save()
            
            # Update resume status
            resume.status = 'analyzed'
            resume.analyzed_at = timezone.now()
            resume.save()
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing resume externally: {e}")
            resume.status = 'failed'
            resume.save()
            return None 