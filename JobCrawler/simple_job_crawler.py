#!/usr/bin/env python3
"""
Simple Job Crawler API Service for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import json
from datetime import datetime

app = FastAPI(
    title="Job Crawler API Service",
    description="Job crawling and market analysis service",
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

# Mock data
mock_jobs = [
    {
        "id": "job_1",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "salary_range": "$120,000 - $180,000",
        "description": "We are looking for a Senior Python Developer with 5+ years of experience...",
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
        "description": "Join our fast-growing startup as a Full Stack Developer...",
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
        "description": "We are seeking a talented Data Scientist to join our team...",
        "requirements": ["Python", "Machine Learning", "SQL", "Statistics"],
        "posted_date": "2024-01-13",
        "source": "Glassdoor"
    }
]

mock_trending_jobs = [
    {
        "title": "AI Engineer",
        "trend_score": 0.95,
        "growth_rate": "+25%",
        "demand": "High"
    },
    {
        "title": "DevOps Engineer", 
        "trend_score": 0.88,
        "growth_rate": "+20%",
        "demand": "High"
    },
    {
        "title": "Product Manager",
        "trend_score": 0.82,
        "growth_rate": "+15%", 
        "demand": "Medium"
    }
]

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
    return {
        "status": "healthy",
        "service": "Job Crawler API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Job Crawler API",
        "version": "1.0.0",
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "crawlers": "healthy"
        }
    }

@app.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    """Search for jobs"""
    try:
        # Filter jobs based on query
        filtered_jobs = []
        for job in mock_jobs:
            if request.query.lower() in job["title"].lower() or request.query.lower() in job["description"].lower():
                filtered_jobs.append(job)
        
        # Limit results
        if request.limit:
            filtered_jobs = filtered_jobs[:request.limit]
        
        return JobSearchResponse(
            jobs=filtered_jobs,
            total=len(filtered_jobs),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@app.get("/jobs/trending/list")
async def get_trending_jobs():
    """Get trending jobs"""
    try:
        return {
            "trending_jobs": mock_trending_jobs,
            "total": len(mock_trending_jobs),
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending jobs: {str(e)}")

@app.post("/market/salary")
async def get_salary_data(request: SalaryRequest):
    """Get salary data for a job title and location"""
    try:
        # Mock salary data
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
        raise HTTPException(status_code=500, detail=f"Failed to get market trends: {str(e)}")

@app.post("/jobs/recommendations/list")
async def get_job_recommendations(request: RecommendationRequest):
    """Get job recommendations based on skills and experience"""
    try:
        # Mock recommendations
        recommendations = [
            {
                "id": "rec_1",
                "title": "Senior Python Developer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "match_score": 0.92,
                "salary_range": "$130,000 - $180,000",
                "matching_skills": ["python", "django", "postgresql"],
                "missing_skills": ["kubernetes"],
                "posted_date": "2024-01-15"
            },
            {
                "id": "rec_2",
                "title": "Full Stack Developer",
                "company": "StartupXYZ",
                "location": "New York, NY", 
                "match_score": 0.85,
                "salary_range": "$110,000 - $150,000",
                "matching_skills": ["python", "react"],
                "missing_skills": ["aws", "docker"],
                "posted_date": "2024-01-14"
            },
            {
                "id": "rec_3",
                "title": "Backend Engineer",
                "company": "BigTech Corp",
                "location": "Seattle, WA",
                "match_score": 0.78,
                "salary_range": "$120,000 - $170,000",
                "matching_skills": ["python", "postgresql"],
                "missing_skills": ["machine learning", "aws"],
                "posted_date": "2024-01-13"
            }
        ]
        
        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "user_skills": request.skills,
            "experience_level": request.experience_level,
            "location": request.location
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_job_crawler:app", host="0.0.0.0", port=8000, reload=True) 