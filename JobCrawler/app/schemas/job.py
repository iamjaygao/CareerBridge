"""
Pydantic schemas for job-related API responses
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobResponse(BaseModel):
    """Job response schema"""
    id: int
    title: str
    company: str
    location: str
    description: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_work: Optional[bool] = None
    source: str
    skills: Optional[List[str]] = None

class JobSearchResponse(BaseModel):
    """Job search response schema"""
    jobs: List[JobResponse]
    total: int
    limit: int
    offset: int

class JobDetailResponse(BaseModel):
    """Detailed job response schema"""
    id: int
    title: str
    company: str
    location: str
    description: str
    requirements: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_work: bool
    source: str
    source_url: Optional[str] = None
    skills: List[str]
    posted_date: Optional[str] = None

class TrendingJobResponse(BaseModel):
    """Trending job response schema"""
    id: int
    title: str
    company: str
    location: str
    trend_score: float
    source: str

class TrendingJobsResponse(BaseModel):
    """Trending jobs list response schema"""
    trending_jobs: List[TrendingJobResponse]
    days: int
    total: int

class JobRecommendationResponse(BaseModel):
    """Job recommendation response schema"""
    id: int
    title: str
    company: str
    location: str
    match_score: float
    skills_match: List[str]
    source: str

class JobRecommendationsResponse(BaseModel):
    """Job recommendations list response schema"""
    recommendations: List[JobRecommendationResponse]
    skills: List[str]
    total: int 