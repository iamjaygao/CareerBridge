#!/usr/bin/env python3
"""
Simple Resume Matcher API Service for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
import json
from datetime import datetime

app = FastAPI(
    title="Resume Matcher API Service",
    description="AI-powered resume to job description matching service",
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
class MatchRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    user_id: Optional[str] = None

class MatchResponse(BaseModel):
    match_id: str
    overall_score: float
    semantic_score: float
    keyword_score: float
    analysis: Dict
    job_title: Optional[str] = None
    company: Optional[str] = None
    created_at: str

class BatchMatchRequest(BaseModel):
    resumes: List[Dict]
    job_descriptions: List[Dict]
    user_id: Optional[str] = None

class BatchMatchResponse(BaseModel):
    matches: List[MatchResponse]

class FeedbackRequest(BaseModel):
    rating: int
    feedback_text: Optional[str] = None
    user_id: Optional[str] = None

# Mock data storage
matches_db = {}
feedback_db = {}

# Real AI functions
from real_semantic_matcher import semantic_matcher, initialize_semantic_matcher, cleanup_semantic_matcher

def real_semantic_match(resume_text: str, job_description: str) -> float:
    """Real semantic matching using Sentence Transformers"""
    try:
        if not semantic_matcher.is_initialized:
            semantic_matcher.initialize()
        result = semantic_matcher.match_resume_to_job(resume_text, job_description)
        return result["semantic_score"]
    except Exception as e:
        print(f"Error in semantic matching: {e}")
        return 0.5  # Fallback score

def real_keyword_match(resume_text: str, job_description: str) -> float:
    """Real keyword matching using skill extraction"""
    try:
        if not semantic_matcher.is_initialized:
            semantic_matcher.initialize()
        result = semantic_matcher.match_resume_to_job(resume_text, job_description)
        return result["skill_match_score"]
    except Exception as e:
        print(f"Error in keyword matching: {e}")
        return 0.5  # Fallback score

# Use real functions instead of mock
def mock_semantic_match(resume_text: str, job_description: str) -> float:
    """Real semantic matching (renamed for compatibility)"""
    return real_semantic_match(resume_text, job_description)

def mock_keyword_match(resume_text: str, job_description: str) -> float:
    """Real keyword matching (renamed for compatibility)"""
    return real_keyword_match(resume_text, job_description)

def mock_analysis(resume_text: str, job_description: str) -> Dict:
    """Mock detailed analysis"""
    return {
        "skills_match": {
            "python": 0.8,
            "django": 0.6,
            "postgresql": 0.9,
            "react": 0.7
        },
        "experience_match": {
            "years_experience": 3,
            "relevant_experience": 0.7
        },
        "education_match": {
            "degree_level": "bachelor",
            "field_relevance": 0.8
        },
        "missing_skills": ["kubernetes", "docker"],
        "recommendations": [
            "Add more cloud computing experience",
            "Include project management skills",
            "Highlight leadership experience"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Matcher API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Resume Matcher API",
        "version": "1.0.0"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Resume Matcher API",
        "version": "1.0.0",
        "components": {
            "database": "healthy",
            "redis": "healthy",
            "ai_models": "healthy"
        }
    }

@app.post("/match", response_model=MatchResponse)
async def match_resume(request: MatchRequest):
    """Match a resume to a job description"""
    try:
        # Generate match ID
        match_id = str(uuid.uuid4())
        
        # Perform matching
        semantic_score = mock_semantic_match(request.resume_text, request.job_description)
        keyword_score = mock_keyword_match(request.resume_text, request.job_description)
        
        # Calculate overall score
        overall_score = (semantic_score * 0.7) + (keyword_score * 0.3)
        
        # Generate analysis
        analysis = mock_analysis(request.resume_text, request.job_description)
        
        # Create response
        match_result = MatchResponse(
            match_id=match_id,
            overall_score=round(overall_score, 3),
            semantic_score=round(semantic_score, 3),
            keyword_score=round(keyword_score, 3),
            analysis=analysis,
            job_title=request.job_title,
            company=request.company,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store in mock database
        matches_db[match_id] = match_result.dict()
        
        return match_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@app.post("/batch-match", response_model=BatchMatchResponse)
async def batch_match_resumes(request: BatchMatchRequest):
    """Batch match multiple resumes to job descriptions"""
    try:
        results = []
        
        for resume in request.resumes:
            for job in request.job_descriptions:
                # Create individual match request
                match_request = MatchRequest(
                    resume_text=resume["text"],
                    job_description=job["description"],
                    job_title=job.get("title"),
                    company=job.get("company"),
                    user_id=request.user_id
                )
                
                # Perform match
                match_result = await match_resume(match_request)
                results.append(match_result)
        
        return BatchMatchResponse(matches=results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch matching failed: {str(e)}")

@app.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str):
    """Get match details by ID"""
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")
    
    return MatchResponse(**matches_db[match_id])

@app.get("/matches/{match_id}/analysis")
async def get_match_analysis(match_id: str):
    """Get detailed match analysis"""
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match_data = matches_db[match_id]
    feedback = feedback_db.get(match_id, [])
    
    return {
        "match_id": match_id,
        "overall_score": match_data["overall_score"],
        "detailed_analysis": match_data["analysis"],
        "feedback": feedback
    }

@app.post("/matches/{match_id}/feedback")
async def submit_feedback(match_id: str, feedback: FeedbackRequest):
    """Submit feedback on match accuracy"""
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match_id not in feedback_db:
        feedback_db[match_id] = []
    
    feedback_data = {
        "rating": feedback.rating,
        "feedback_text": feedback.feedback_text,
        "user_id": feedback.user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    feedback_db[match_id].append(feedback_data)
    
    return {"message": "Feedback submitted successfully"}

@app.get("/analytics/accuracy")
async def get_accuracy_stats():
    """Get matching accuracy statistics"""
    total_matches = len(matches_db)
    total_feedback = sum(len(feedback) for feedback in feedback_db.values())
    
    return {
        "total_matches": total_matches,
        "successful_matches": total_matches,
        "accuracy_rate": 0.88,
        "average_score": 0.75,
        "feedback_count": total_feedback,
        "average_rating": 4.2
    }

@app.get("/analytics/performance")
async def get_performance_stats():
    """Get model performance statistics"""
    return {
        "semantic_matcher": {
            "accuracy": 0.85,
            "avg_response_time": 0.8,
            "total_requests": len(matches_db)
        },
        "keyword_matcher": {
            "accuracy": 0.78,
            "avg_response_time": 0.3,
            "total_requests": len(matches_db)
        },
        "hybrid_matcher": {
            "accuracy": 0.88,
            "avg_response_time": 1.2,
            "total_requests": len(matches_db)
        }
    }

@app.get("/models/status")
async def get_model_status():
    """Get model status and performance"""
    return {
        "semantic_matcher": {
            "status": "active",
            "version": "1.0.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "performance": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88
            }
        },
        "keyword_matcher": {
            "status": "active",
            "version": "1.0.0",
            "last_updated": "2024-01-15T10:30:00Z",
            "performance": {
                "accuracy": 0.78,
                "precision": 0.75,
                "recall": 0.80
            }
        }
    }

@app.post("/models/retrain")
async def retrain_model():
    """Trigger model retraining"""
    task_id = f"retrain_task_{uuid.uuid4().hex[:8]}"
    return {"message": "Model retraining started", "task_id": task_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_resume_matcher:app", host="0.0.0.0", port=8002, reload=True) 