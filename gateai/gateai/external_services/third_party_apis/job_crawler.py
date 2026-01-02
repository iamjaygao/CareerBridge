"""
Job Crawler API Integration

This module provides integration with job crawling APIs to fetch
job listings, market data, and industry trends.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..config import config

logger = logging.getLogger(__name__)


class JobCrawlerService:
    """Job crawler API service integration"""
    
    def __init__(self):
        self.api_key = config.job_crawler.api_key
        self.base_url = config.job_crawler.base_url
        self.timeout = config.job_crawler.timeout
        self.rate_limit = config.job_crawler.rate_limit
        
        if not self.api_key:
            logger.warning("Job crawler API key not configured")
    
    def search_jobs(
        self,
        query: str = None,
        filters: Dict = None,
        page: int = 1,
        user = None
    ) -> Dict[str, Any]:
        """
        Search for jobs using various criteria
        
        Args:
            query: Job title or keywords
            filters: Dictionary of filters (location, company, etc.)
            page: Page number for pagination
            user: User object (for logging)
        
        Returns:
            Job search results
        """
        try:
            import httpx
            
            # Prepare request data
            request_data = {
                "query": query or "python developer",
                "location": filters.get('location', 'San Francisco') if filters else 'San Francisco',
                "limit": 10
            }
            
            # Make request to JobCrawler API
            url = f"{self.base_url}/jobs/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return {
                "jobs": [],
                "total": 0,
                "query": query or "python developer"
            }
    
    def get_job_details(self, job_id: str, user = None) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        try:
            import httpx
            
            url = f"{self.base_url}/jobs/{job_id}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Job details retrieval failed: {e}")
            return {
                "id": job_id,
                "error": str(e)
            }
    
    def get_trending_jobs(self, user = None) -> List[Dict[str, Any]]:
        """Get trending jobs"""
        try:
            import httpx
            
            url = f"{self.base_url}/jobs/trending/list"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get("trending_jobs", [])
                
        except Exception as e:
            logger.error(f"Failed to get trending jobs: {e}")
            return []
    
    def get_salary_data(
        self,
        job_title: str,
        location: str = None,
        user = None
    ) -> Dict[str, Any]:
        """Get salary data for a specific job title"""
        try:
            import httpx
            
            url = f"{self.base_url}/market/salary"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            request_data = {
                "job_title": job_title,
                "location": location or "San Francisco"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Salary data retrieval failed: {e}")
            return {
                "job_title": job_title,
                "location": location,
                "average_salary": 0,
                "error": str(e)
            }
    
    def get_skill_demand(
        self,
        job_title: str,
        location: str = None,
        user = None
    ) -> Dict[str, Any]:
        """Get skill demand data for a specific job title"""
        try:
            import httpx
            
            url = f"{self.base_url}/market/skills"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            request_data = {
                "job_title": job_title,
                "location": location or "New York"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Skill demand data retrieval failed: {e}")
            return {
                "job_title": job_title,
                "location": location,
                "top_skills": [],
                "error": str(e)
            }
    
    def get_market_trends(self, user = None) -> Dict[str, Any]:
        """Get market trends and insights"""
        try:
            import httpx
            
            url = f"{self.base_url}/market/trends"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Market trends retrieval failed: {e}")
            return {
                "hot_industries": [],
                "growing_roles": [],
                "error": str(e)
            }
    
    def get_recommended_jobs(
        self,
        skills: List[str],
        experience_level: str,
        location: str = None,
        user = None
    ) -> List[Dict[str, Any]]:
        """Get job recommendations based on user profile"""
        try:
            import httpx
            
            url = f"{self.base_url}/jobs/recommendations/list"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            request_data = {
                "skills": skills,
                "experience_level": experience_level,
                "location": location or "San Francisco"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=request_data, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get("recommendations", [])
                
        except Exception as e:
            logger.error(f"Job recommendations failed: {e}")
            return []
    
    def check_health(self) -> Dict[str, Any]:
        """Check job crawler service health"""
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
job_crawler_service = JobCrawlerService() 