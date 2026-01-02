"""
Resume Matcher API Integration

This module provides integration with resume matching APIs to perform
resume-job matching, skill analysis, and recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..config import config

logger = logging.getLogger(__name__)


class ResumeMatcherService:
    """Resume matcher API service integration"""
    
    def __init__(self):
        self.api_key = config.resume_matcher.api_key
        self.base_url = config.resume_matcher.base_url
        self.timeout = config.resume_matcher.timeout
        self.confidence_threshold = config.resume_matcher.confidence_threshold
        
        if not self.api_key:
            logger.warning("Resume matcher API key not configured")
    
    def match_resume_to_jd(
        self,
        resume_text: str,
        job_description: str,
        job_title: str = None,
        company: str = None,
        user = None
    ) -> Dict[str, Any]:
        """
        Match a resume to a job description
        
        Args:
            resume_text: Resume text content
            job_description: Job description text
            job_title: Job title
            company: Company name
            user: User object (for logging)
        
        Returns:
            Match result with scores and analysis
        """
        try:
            import httpx
            
            # Prepare request data
            request_data = {
                "resume_text": resume_text,
                "job_description": job_description,
                "job_title": job_title or "Software Engineer",
                "company": company or "Tech Company"
            }
            
            # Make request to ResumeMatcher API
            url = f"{self.base_url}/match"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Resume matching failed: {e}")
            return {
                "match_id": "error",
                "overall_score": 0.0,
                "semantic_score": 0.0,
                "keyword_score": 0.0,
                "analysis": {},
                "error": str(e)
            }
    
    def batch_match_resumes(
        self,
        resumes: List[Dict[str, str]],
        job_descriptions: List[Dict[str, str]],
        user = None
    ) -> List[Dict[str, Any]]:
        """
        Batch match multiple resumes to job descriptions
        
        Args:
            resumes: List of resume data
            job_descriptions: List of job description data
            user: User object (for logging)
        
        Returns:
            List of match results
        """
        try:
            import httpx
            
            # Prepare request data
            request_data = {
                "resumes": resumes,
                "job_descriptions": job_descriptions
            }
            
            # Make request to ResumeMatcher API
            url = f"{self.base_url}/match/batch"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get("matches", [])
                
        except Exception as e:
            logger.error(f"Batch resume matching failed: {e}")
            return []
    
    def get_match_analysis(self, match_id: str, user = None) -> Dict[str, Any]:
        """Get detailed analysis for a specific match"""
        try:
            import httpx
            
            url = f"{self.base_url}/match/{match_id}/analysis"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Match analysis retrieval failed: {e}")
            return {
                "match_id": match_id,
                "analysis": {},
                "error": str(e)
            }
    
    def submit_feedback(
        self,
        match_id: str,
        feedback_text: str,
        rating: int = None,
        user = None
    ) -> Dict[str, Any]:
        """Submit feedback for a match"""
        try:
            import httpx
            
            request_data = {
                "feedback_text": feedback_text,
                "rating": rating
            }
            
            url = f"{self.base_url}/match/{match_id}/feedback"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Feedback submission failed: {e}")
            return {
                "match_id": match_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_accuracy_stats(self, user = None) -> Dict[str, Any]:
        """Get matching accuracy statistics"""
        try:
            import httpx
            
            url = f"{self.base_url}/analytics/accuracy"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Accuracy stats retrieval failed: {e}")
            return {
                "overall_accuracy": 0.0,
                "total_matches": 0,
                "error": str(e)
            }
    
    def get_performance_stats(self, user = None) -> Dict[str, Any]:
        """Get model performance statistics"""
        try:
            import httpx
            
            url = f"{self.base_url}/analytics/performance"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Performance stats retrieval failed: {e}")
            return {
                "average_response_time": 0.0,
                "total_requests": 0,
                "error": str(e)
            }
    
    def check_health(self) -> Dict[str, Any]:
        """Check resume matcher service health"""
        try:
            import httpx
            
            url = f"{self.base_url}/health"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
resume_matcher_service = ResumeMatcherService() 