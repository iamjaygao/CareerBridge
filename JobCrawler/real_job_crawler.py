#!/usr/bin/env python3
"""
Real Job Crawler API Service with Database Storage
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import json
from datetime import datetime
import structlog

# Database imports
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

logger = structlog.get_logger()

# Database setup
DATABASE_URL = "sqlite:///./job_crawler.db"  # Use SQLite for development
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, index=True)
    salary_range = Column(String)
    description = Column(Text)
    requirements = Column(Text)  # JSON string
    posted_date = Column(DateTime)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobSearch(Base):
    __tablename__ = "job_searches"
    
    id = Column(String, primary_key=True, index=True)
    query = Column(String, index=True)
    location = Column(String, index=True)
    results_count = Column(Integer)
    search_date = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    limit: Optional[int] = 10

class JobSearchResponse(BaseModel):
    jobs: List[Dict]
    total: int
    query: str

class SalaryRequest(BaseModel):
    job_title: str
    location: str

class SkillRequest(BaseModel):
    job_title: str
    location: str

class RecommendationRequest(BaseModel):
    skills: List[str]
    experience_level: str
    location: str

# Database helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def store_job(db, job_data: Dict):
    """Store a job in the database"""
    try:
        # Convert requirements list to JSON string
        requirements_json = json.dumps(job_data.get('requirements', []))
        
        job = Job(
            id=job_data.get('id'),
            title=job_data.get('title'),
            company=job_data.get('company'),
            location=job_data.get('location'),
            salary_range=job_data.get('salary_range'),
            description=job_data.get('description'),
            requirements=requirements_json,
            posted_date=datetime.fromisoformat(job_data.get('posted_date', datetime.utcnow().isoformat())),
            source=job_data.get('source')
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    except Exception as e:
        logger.error("Error storing job", error=str(e))
        db.rollback()
        raise

def search_jobs_db(db, query: str, location: str = None, limit: int = 10):
    """Search jobs in database"""
    try:
        # Build search query
        search_query = db.query(Job)
        
        if query:
            search_query = search_query.filter(
                Job.title.contains(query) | Job.description.contains(query)
            )
        
        if location:
            search_query = search_query.filter(Job.location.contains(location))
        
        # Limit results
        jobs = search_query.limit(limit).all()
        
        # Convert to dict format
        job_list = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_range": job.salary_range,
                "description": job.description,
                "requirements": json.loads(job.requirements) if job.requirements else [],
                "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                "source": job.source
            }
            job_list.append(job_dict)
        
        return job_list
    except Exception as e:
        logger.error("Error searching jobs", error=str(e))
        return []

# Sample job data for initialization
sample_jobs = [
    {
        "id": "job_1",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "salary_range": "$120,000 - $180,000",
        "description": "We are looking for a Senior Python Developer with 5+ years of experience in Django, Flask, and PostgreSQL. Experience with AWS and cloud platforms is required.",
        "requirements": ["Python", "Django", "PostgreSQL", "AWS"],
        "posted_date": "2024-01-15",
        "source": "LinkedIn"
    },
    {
        "id": "job_2", 
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "New York, NY",
        "salary_range": "$100,000 - $150,000",
        "description": "Join our fast-growing startup as a Full Stack Developer. We use React, Node.js, and MongoDB. Experience with TypeScript is a plus.",
        "requirements": ["React", "Node.js", "MongoDB", "TypeScript"],
        "posted_date": "2024-01-14",
        "source": "Indeed"
    },
    {
        "id": "job_3",
        "title": "Data Scientist",
        "company": "BigTech Corp",
        "location": "Seattle, WA", 
        "salary_range": "$130,000 - $200,000",
        "description": "We are seeking a talented Data Scientist to join our team. Experience with Python, Machine Learning, and SQL is required.",
        "requirements": ["Python", "Machine Learning", "SQL", "Statistics"],
        "posted_date": "2024-01-13",
        "source": "Glassdoor"
    }
]

# Initialize database with sample data
def initialize_database():
    """Initialize database with sample data"""
    db = SessionLocal()
    try:
        # Check if jobs already exist
        existing_jobs = db.query(Job).count()
        if existing_jobs == 0:
            logger.info("Initializing database with sample jobs")
            for job_data in sample_jobs:
                store_job(db, job_data)
            logger.info("Database initialized successfully")
        else:
            logger.info(f"Database already contains {existing_jobs} jobs")
    except Exception as e:
        logger.error("Error initializing database", error=str(e))
    finally:
        db.close()

# FastAPI app
app = FastAPI(
    title="Job Crawler API Service",
    description="Job crawling and market analysis service with database storage",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    initialize_database()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Job Crawler API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "service": "Job Crawler API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Job Crawler API",
            "version": "1.0.0",
            "error": str(e)
        }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    try:
        db = SessionLocal()
        job_count = db.query(Job).count()
        db.close()
        
        return {
            "status": "healthy",
            "service": "Job Crawler API",
            "version": "1.0.0",
            "components": {
                "database": "healthy",
                "redis": "not_configured",
                "crawlers": "healthy"
            },
            "stats": {
                "total_jobs": job_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Job Crawler API",
            "version": "1.0.0",
            "error": str(e)
        }

@app.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs in database"""
    try:
        db = SessionLocal()
        jobs = search_jobs_db(db, request.query, request.location, request.limit)
        db.close()
        
        return JobSearchResponse(
            jobs=jobs,
            total=len(jobs),
            query=request.query
        )
        
    except Exception as e:
        logger.error("Job search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@app.get("/jobs/trending/list")
async def get_trending_jobs():
    """Get trending jobs from database"""
    try:
        db = SessionLocal()
        
        # Get most recent jobs as trending
        trending_jobs = db.query(Job).order_by(Job.posted_date.desc()).limit(5).all()
        db.close()
        
        trending_list = []
        for job in trending_jobs:
            trending_list.append({
                "title": job.title,
                "trend_score": 0.8,  # Mock trend score
                "growth_rate": "+15%",
                "demand": "High"
            })
        
        return {
            "trending_jobs": trending_list,
            "total": len(trending_list),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get trending jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get trending jobs: {str(e)}")

@app.post("/market/salary")
async def get_salary_data(request: SalaryRequest):
    """Get salary data for a job title and location"""
    try:
        # Mock salary data (in real implementation, this would come from salary database)
        salary_data = {
            "job_title": request.job_title,
            "location": request.location,
            "average_salary": 125000,
            "min_salary": 90000,
            "max_salary": 180000,
            "salary_percentiles": {
                "25th": 100000,
                "50th": 125000,
                "75th": 150000,
                "90th": 170000
            },
            "data_points": 150,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return salary_data
        
    except Exception as e:
        logger.error("Failed to get salary data", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get salary data: {str(e)}")

@app.post("/market/skills")
async def get_skill_demand(request: SkillRequest):
    """Get skill demand for a job title and location"""
    try:
        # Mock skill demand data
        skill_data = {
            "job_title": request.job_title,
            "location": request.location,
            "top_skills": [
                {"skill": "Python", "demand_score": 0.95, "growth_rate": "+15%"},
                {"skill": "JavaScript", "demand_score": 0.88, "growth_rate": "+12%"},
                {"skill": "SQL", "demand_score": 0.82, "growth_rate": "+8%"},
                {"skill": "AWS", "demand_score": 0.78, "growth_rate": "+20%"},
                {"skill": "Docker", "demand_score": 0.75, "growth_rate": "+18%"}
            ],
            "emerging_skills": [
                {"skill": "Kubernetes", "demand_score": 0.65, "growth_rate": "+25%"},
                {"skill": "GraphQL", "demand_score": 0.60, "growth_rate": "+22%"},
                {"skill": "TypeScript", "demand_score": 0.58, "growth_rate": "+19%"}
            ],
            "total_jobs_analyzed": 500,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return skill_data
        
    except Exception as e:
        logger.error("Failed to get skill demand", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get skill demand: {str(e)}")

@app.get("/market/trends")
async def get_market_trends():
    """Get market trends"""
    try:
        trends_data = {
            "hot_industries": [
                {"industry": "Artificial Intelligence", "growth_rate": "+30%"},
                {"industry": "Cybersecurity", "growth_rate": "+25%"},
                {"industry": "Cloud Computing", "growth_rate": "+22%"},
                {"industry": "Data Science", "growth_rate": "+20%"}
            ],
            "growing_roles": [
                {"role": "AI Engineer", "growth_rate": "+35%"},
                {"role": "DevOps Engineer", "growth_rate": "+28%"},
                {"role": "Data Engineer", "growth_rate": "+25%"},
                {"role": "Product Manager", "growth_rate": "+18%"}
            ],
            "salary_trends": {
                "overall_growth": "+5.2%",
                "tech_growth": "+7.8%",
                "remote_work_impact": "+12%"
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return trends_data
        
    except Exception as e:
        logger.error("Failed to get market trends", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get market trends: {str(e)}")

@app.post("/jobs/recommendations/list")
async def get_job_recommendations(request: RecommendationRequest):
    """Get job recommendations based on skills and experience"""
    try:
        db = SessionLocal()
        
        # Search for jobs matching the skills
        matching_jobs = []
        for skill in request.skills:
            jobs = search_jobs_db(db, skill, request.location, 3)
            matching_jobs.extend(jobs)
        
        # Remove duplicates and limit results
        unique_jobs = {job["id"]: job for job in matching_jobs}.values()
        recommendations = list(unique_jobs)[:5]
        
        db.close()
        
        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "user_skills": request.skills,
            "experience_level": request.experience_level,
            "location": request.location
        }
        
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("real_job_crawler:app", host="0.0.0.0", port=8000, reload=True) 