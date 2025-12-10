#!/usr/bin/env python3
"""
Start script for Resume Matcher API Service
"""

import os
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Set default environment variables if not present
    os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost/resume_matcher_db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("API_KEY", "dev-api-key")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 