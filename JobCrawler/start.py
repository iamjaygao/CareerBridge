#!/usr/bin/env python3
"""
Simple startup script for Job Crawler API Service
"""

import uvicorn
import os

if __name__ == "__main__":
    # Set default environment variables if not already set
    os.environ.setdefault("DATABASE_URL", "sqlite:///./job_crawler.db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("API_KEY", "dev-api-key")
    os.environ.setdefault("DEBUG", "true")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 