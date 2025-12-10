"""
Job-related API endpoints
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.services.job_service import JobService
from app.schemas.job import JobResponse, JobSearchResponse, JobRecommendationResponse, TrendingJobResponse

logger = structlog.get_logger()
router = APIRouter()

@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    keywords: Optional[str] = Query(None, description="Search keywords"),
    location: Optional[str] = Query(None, description="Job location"),
    company: Optional[str] = Query(None, description="Company name"),
    job_type: Optional[str] = Query(None, description="Job type (full-time, part-time, etc.)"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    remote_work: Optional[bool] = Query(None, description="Remote work option"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Search for jobs with various filters"""
    try:
        job_service = JobService(db)
        jobs = await job_service.search_jobs(
            keywords=keywords,
            location=location,
            company=company,
            job_type=job_type,
            experience_level=experience_level,
            remote_work=remote_work,
            limit=limit,
            offset=offset
        )
        
        return JobSearchResponse(
            jobs=jobs,
            total=len(jobs),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error("Job search failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_details(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific job"""
    try:
        job_service = JobService(db)
        job = await job_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get job details failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trending/list", response_model=TrendingJobResponse)
async def get_trending_jobs(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Number of trending jobs"),
    db: AsyncSession = Depends(get_db)
):
    """Get trending jobs based on recent activity"""
    try:
        job_service = JobService(db)
        trending_jobs = await job_service.get_trending_jobs(days=days, limit=limit)
        
        return TrendingJobResponse(
            trending_jobs=trending_jobs,
            days=days,
            total=len(trending_jobs)
        )
    except Exception as e:
        logger.error("Get trending jobs failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/recommendations/list", response_model=JobRecommendationResponse)
async def get_job_recommendations(
    skills: str = Query(..., description="Comma-separated list of skills"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    location: Optional[str] = Query(None, description="Preferred location"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of recommendations"),
    db: AsyncSession = Depends(get_db)
):
    """Get job recommendations based on skills and preferences"""
    try:
        skill_list = [skill.strip() for skill in skills.split(",")]
        job_service = JobService(db)
        
        recommendations = await job_service.get_job_recommendations(
            skills=skill_list,
            experience_level=experience_level,
            location=location,
            max_results=max_results
        )
        
        return JobRecommendationResponse(
            recommendations=recommendations,
            skills=skill_list,
            total=len(recommendations)
        )
    except Exception as e:
        logger.error("Get job recommendations failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") 