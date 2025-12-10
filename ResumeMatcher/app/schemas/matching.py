"""
Pydantic schemas for matching API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class MatchRequest(BaseModel):
    """Request schema for single match"""
    resume_text: str = Field(..., description="Resume text content")
    job_description: str = Field(..., description="Job description text")
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    user_id: Optional[str] = Field(None, description="User ID")

class MatchResponse(BaseModel):
    """Response schema for single match"""
    match_id: str = Field(..., description="Unique match ID")
    overall_score: float = Field(..., description="Overall match score (0-1)")
    semantic_score: float = Field(..., description="Semantic match score")
    keyword_score: float = Field(..., description="Keyword match score")
    analysis: Dict = Field(..., description="Detailed analysis")
    job_title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    created_at: str = Field(..., description="Match creation timestamp")

class BatchMatchRequest(BaseModel):
    """Request schema for batch matching"""
    resumes: List[Dict] = Field(..., description="List of resume data")
    job_descriptions: List[Dict] = Field(..., description="List of job descriptions")
    user_id: Optional[str] = Field(None, description="User ID")

class BatchMatchResponse(BaseModel):
    """Response schema for batch matching"""
    matches: List[MatchResponse] = Field(..., description="List of match results")

class MatchAnalysisResponse(BaseModel):
    """Response schema for detailed match analysis"""
    match_id: str = Field(..., description="Match ID")
    overall_score: float = Field(..., description="Overall match score")
    detailed_analysis: Dict = Field(..., description="Detailed analysis")
    feedback: List[Dict] = Field(..., description="User feedback")

class FeedbackRequest(BaseModel):
    """Request schema for match feedback"""
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="Feedback text")
    user_id: Optional[str] = Field(None, description="User ID") 