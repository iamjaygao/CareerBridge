"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import structlog

from app.core.database import get_db, get_redis
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "Resume Matcher API",
        "version": settings.VERSION
    }

@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Detailed health check with database and Redis status"""
    health_status = {
        "status": "healthy",
        "service": "Resume Matcher API",
        "version": settings.VERSION,
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
    
    # Check AI services
    if settings.OPENAI_API_KEY:
        health_status["components"]["openai"] = "configured"
    else:
        health_status["components"]["openai"] = "not_configured"
    
    return health_status 