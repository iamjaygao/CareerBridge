"""
Market data API endpoints
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from app.api.dependencies import verify_api_key
from app.core.database import get_db
from app.services.market_service import MarketService

logger = structlog.get_logger()
router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.get("/salary")
async def get_salary_data(
    job_title: str = Query(..., description="Job title to analyze"),
    location: Optional[str] = Query(None, description="Location for salary data"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    db: AsyncSession = Depends(get_db)
):
    """Get salary data for a specific job title and location"""
    try:
        market_service = MarketService(db)
        salary_data = await market_service.get_salary_data(
            job_title=job_title,
            location=location,
            experience_level=experience_level
        )
        
        return salary_data
    except Exception as e:
        logger.error("Get salary data failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/skills")
async def get_skill_demand(
    skills: str = Query(..., description="Comma-separated list of skills"),
    timeframe: str = Query("30d", description="Timeframe for analysis (7d, 30d, 90d)"),
    location: Optional[str] = Query(None, description="Location for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """Get skill demand analysis"""
    try:
        skill_list = [skill.strip() for skill in skills.split(",")]
        market_service = MarketService(db)
        
        skill_demand = await market_service.get_skill_demand(
            skills=skill_list,
            timeframe=timeframe,
            location=location
        )
        
        return skill_demand
    except Exception as e:
        logger.error("Get skill demand failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trends")
async def get_market_trends(
    timeframe: str = Query("30d", description="Timeframe for trends"),
    location: Optional[str] = Query(None, description="Location for trends"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    db: AsyncSession = Depends(get_db)
):
    """Get general market trends"""
    try:
        market_service = MarketService(db)
        trends = await market_service.get_market_trends(
            timeframe=timeframe,
            location=location,
            industry=industry
        )
        
        return trends
    except Exception as e:
        logger.error("Get market trends failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") 
