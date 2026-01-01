"""
Resume Matcher API Service - Main Application
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import matching, analytics, health, models
from app.services.matching_service import MatchingService
from app.utils.logging import setup_logging
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Setup logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Resume Matcher API Service")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize matching service
    await MatchingService.initialize()
    
    logger.info("Resume Matcher API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Matcher API Service")
    await MatchingService.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Resume Matcher API Service",
    description="AI-powered resume to job description matching service",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(matching.router, prefix="/match", tags=["matching"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(models.router, prefix="/models", tags=["models"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Matcher API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 
