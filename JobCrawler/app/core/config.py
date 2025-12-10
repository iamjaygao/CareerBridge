"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Job Crawler API Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/job_crawler_db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # API
    API_KEY: str = "dev-api-key"
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8001"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Scraping
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_DELAY: int = 1
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # External APIs
    INDEED_API_KEY: Optional[str] = None
    LINKEDIN_API_KEY: Optional[str] = None
    GLASSDOOR_API_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 