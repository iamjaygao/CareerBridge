"""
Job Crawler API Integration

This module provides integration with job crawling APIs to fetch
job listings, market data, and industry trends.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..config import config
from ..utils import (
    retry_on_failure, 
    log_api_call, 
    ExternalServiceError, 
    make_api_request,
    create_headers,
    parse_pagination_params
)

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
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("JobCrawler", "jobs/search", "GET")
    def search_jobs(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        remote: Optional[bool] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for jobs using various criteria
        
        Args:
            keywords: Job title or keywords
            location: Job location
            company: Company name
            job_type: Full-time, part-time, contract, etc.
            experience_level: Entry, mid, senior, etc.
            salary_min: Minimum salary
            salary_max: Maximum salary
            remote: Remote work option
            page: Page number for pagination
            page_size: Number of results per page
        
        Returns:
            Job search results
        """
        if not self.api_key:
            raise ExternalServiceError("Job crawler API key not configured", "job_crawler")
        
        url = f"{self.base_url}/jobs/search"
        headers = create_headers(self.api_key)
        
        # Prepare query parameters
        params = {}
        
        if keywords:
            params["q"] = keywords
        if location:
            params["location"] = location
        if company:
            params["company"] = company
        if job_type:
            params["job_type"] = job_type
        if experience_level:
            params["experience_level"] = experience_level
        if salary_min:
            params["salary_min"] = salary_min
        if salary_max:
            params["salary_max"] = salary_max
        if remote is not None:
            params["remote"] = remote
        
        # Add pagination parameters
        pagination_params = parse_pagination_params(page, page_size)
        params.update(pagination_params)
        
        try:
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                data=None,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            logger.info(f"Job search completed: {len(response.get('jobs', []))} results")
            return response
            
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            raise ExternalServiceError(f"Job search failed: {e}", "job_crawler")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("JobCrawler", "jobs/{job_id}", "GET")
    def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job
        
        Args:
            job_id: Unique job identifier
        
        Returns:
            Detailed job information
        """
        if not self.api_key:
            raise ExternalServiceError("Job crawler API key not configured", "job_crawler")
        
        url = f"{self.base_url}/jobs/{job_id}"
        headers = create_headers(self.api_key)
        
        try:
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                data=None,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            logger.info(f"Job details retrieved for job ID: {job_id}")
            return response
            
        except Exception as e:
            logger.error(f"Job details retrieval failed: {e}")
            raise ExternalServiceError(f"Job details retrieval failed: {e}", "job_crawler")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("JobCrawler", "jobs/trending", "GET")
    def get_trending_jobs(
        self,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trending jobs based on recent activity
        
        Args:
            location: Location filter
            industry: Industry filter
            days: Number of days to look back
        
        Returns:
            Trending jobs data
        """
        if not self.api_key:
            raise ExternalServiceError("Job crawler API key not configured", "job_crawler")
        
        url = f"{self.base_url}/jobs/trending"
        headers = create_headers(self.api_key)
        
        params = {"days": days}
        if location:
            params["location"] = location
        if industry:
            params["industry"] = industry
        
        try:
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                data=None,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            logger.info(f"Trending jobs retrieved for {days} days")
            return response
            
        except Exception as e:
            logger.error(f"Trending jobs retrieval failed: {e}")
            raise ExternalServiceError(f"Trending jobs retrieval failed: {e}", "job_crawler")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("JobCrawler", "market/salary", "GET")
    def get_salary_data(
        self,
        job_title: str,
        location: Optional[str] = None,
        experience_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get salary data for a specific job title
        
        Args:
            job_title: Job title to analyze
            location: Location for salary data
            experience_level: Experience level filter
        
        Returns:
            Salary data and statistics
        """
        if not self.api_key:
            raise ExternalServiceError("Job crawler API key not configured", "job_crawler")
        
        url = f"{self.base_url}/market/salary"
        headers = create_headers(self.api_key)
        
        params = {"job_title": job_title}
        if location:
            params["location"] = location
        if experience_level:
            params["experience_level"] = experience_level
        
        try:
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                data=None,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            logger.info(f"Salary data retrieved for: {job_title}")
            return response
            
        except Exception as e:
            logger.error(f"Salary data retrieval failed: {e}")
            raise ExternalServiceError(f"Salary data retrieval failed: {e}", "job_crawler")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("JobCrawler", "market/skills", "GET")
    def get_skill_demand(
        self,
        skills: List[str],
        location: Optional[str] = None,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get demand data for specific skills
        
        Args:
            skills: List of skills to analyze
            location: Location filter
            timeframe: Time period for analysis (7d, 30d, 90d)
        
        Returns:
            Skill demand data
        """
        if not self.api_key:
            raise ExternalServiceError("Job crawler API key not configured", "job_crawler")
        
        url = f"{self.base_url}/market/skills"
        headers = create_headers(self.api_key)
        
        params = {
            "skills": ",".join(skills),
            "timeframe": timeframe
        }
        if location:
            params["location"] = location
        
        try:
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                data=None,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            logger.info(f"Skill demand data retrieved for: {skills}")
            return response
            
        except Exception as e:
            logger.error(f"Skill demand data retrieval failed: {e}")
            raise ExternalServiceError(f"Skill demand data retrieval failed: {e}", "job_crawler")
    
    def get_recommended_jobs(
        self,
        user_skills: List[str],
        user_experience: str,
        preferred_location: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get job recommendations based on user profile
        
        Args:
            user_skills: User's skills
            user_experience: User's experience level
            preferred_location: Preferred job location
            max_results: Maximum number of recommendations
        
        Returns:
            List of recommended jobs
        """
        try:
            # Search for jobs matching user skills
            keywords = " OR ".join(user_skills[:3])  # Use top 3 skills
            search_results = self.search_jobs(
                keywords=keywords,
                location=preferred_location,
                experience_level=user_experience,
                page_size=max_results
            )
            
            jobs = search_results.get("jobs", [])
            
            # Score jobs based on skill match
            scored_jobs = []
            for job in jobs:
                score = self._calculate_job_match_score(job, user_skills)
                job["match_score"] = score
                scored_jobs.append(job)
            
            # Sort by match score
            scored_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            return scored_jobs[:max_results]
            
        except Exception as e:
            logger.error(f"Job recommendations failed: {e}")
            return []
    
    def _calculate_job_match_score(self, job: Dict[str, Any], user_skills: List[str]) -> float:
        """Calculate match score between job and user skills"""
        job_skills = job.get("skills", [])
        job_description = job.get("description", "").lower()
        
        # Count matching skills
        matching_skills = 0
        for skill in user_skills:
            if skill.lower() in job_description or skill.lower() in [s.lower() for s in job_skills]:
                matching_skills += 1
        
        # Calculate score (0-100)
        if not user_skills:
            return 0.0
        
        score = (matching_skills / len(user_skills)) * 100
        return min(score, 100.0)
    
    def check_health(self) -> Dict[str, Any]:
        """Check job crawler service health"""
        try:
            if not self.api_key:
                return {
                    "status": "unhealthy",
                    "error": "API key not configured"
                }
            
            # Simple health check
            url = f"{self.base_url}/health"
            headers = create_headers(self.api_key)
            
            response = make_api_request(
                url=url,
                method="GET",
                headers=headers,
                timeout=self.timeout,
                service="JobCrawler"
            )
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "rate_limit": self.rate_limit
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
job_crawler_service = JobCrawlerService() 