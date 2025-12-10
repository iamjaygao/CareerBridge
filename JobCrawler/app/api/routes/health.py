"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "Job Crawler API",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Detailed health check with database and Redis status"""
    health_status = {
        "status": "healthy",
        "service": "Job Crawler API",
        "version": "1.0.0",
        "components": {}
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["components"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    return health_status 