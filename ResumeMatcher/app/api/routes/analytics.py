"""
Analytics API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()
logger = structlog.get_logger()

@router.get("/accuracy")
async def get_accuracy_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get matching accuracy statistics"""
    try:
        stats = await AnalyticsService.get_accuracy_stats(db)
        return stats
    except Exception as e:
        logger.error("Get accuracy stats failed", error=str(e))
        return {"error": "Failed to retrieve accuracy statistics"}

@router.get("/performance")
async def get_performance_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get model performance statistics"""
    try:
        stats = await AnalyticsService.get_performance_stats(db)
        return stats
    except Exception as e:
        logger.error("Get performance stats failed", error=str(e))
        return {"error": "Failed to retrieve performance statistics"} 