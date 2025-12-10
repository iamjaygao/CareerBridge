"""
Matching API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.core.database import get_db
from app.services.matching_service import MatchingService
from app.schemas.matching import (
    MatchRequest, MatchResponse, BatchMatchRequest, 
    BatchMatchResponse, MatchAnalysisResponse, FeedbackRequest
)

router = APIRouter()
logger = structlog.get_logger()

@router.post("/", response_model=MatchResponse)
async def match_resume(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Match a resume to a job description"""
    try:
        match_result = await MatchingService.match_resume(
            resume_text=request.resume_text,
            job_description=request.job_description,
            job_title=request.job_title,
            company=request.company,
            user_id=request.user_id,
            db=db
        )
        return match_result
    except Exception as e:
        logger.error("Match request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Matching failed"
        )

@router.post("/batch", response_model=BatchMatchResponse)
async def batch_match_resumes(
    request: BatchMatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch match multiple resumes to job descriptions"""
    try:
        results = await MatchingService.batch_match(
            resumes=request.resumes,
            job_descriptions=request.job_descriptions,
            user_id=request.user_id,
            db=db
        )
        return BatchMatchResponse(matches=results)
    except Exception as e:
        logger.error("Batch match request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch matching failed"
        )

@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get match details by ID"""
    try:
        match_result = await MatchingService.get_match(match_id, db)
        if not match_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        return match_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get match failed", match_id=match_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match"
        )

@router.get("/{match_id}/analysis", response_model=MatchAnalysisResponse)
async def get_match_analysis(
    match_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed match analysis"""
    try:
        analysis = await MatchingService.get_match_analysis(match_id, db)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match analysis not found"
            )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get match analysis failed", match_id=match_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match analysis"
        )

@router.post("/{match_id}/feedback")
async def submit_feedback(
    match_id: str,
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on match accuracy"""
    try:
        await MatchingService.submit_feedback(
            match_id=match_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback_text,
            user_id=feedback.user_id,
            db=db
        )
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error("Submit feedback failed", match_id=match_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        ) 