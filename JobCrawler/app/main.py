"""
Job Crawler API Service - Main Application
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import jobs, market, health
from app.services.crawler import CrawlerService
from app.utils.logging import setup_logging
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Setup logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Job Crawler API Service")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize crawler service
    await CrawlerService.initialize()
    
    logger.info("Job Crawler API Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Job Crawler API Service")
    await CrawlerService.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Job Crawler API Service",
    description="A microservice for crawling and analyzing job data from multiple sources",
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
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(market.router, prefix="/market", tags=["market"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Job Crawler API Service",
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
    uvicorn.run(app, host="0.0.0.0", port=8000) 
