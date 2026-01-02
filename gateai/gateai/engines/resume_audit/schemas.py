"""
Pydantic schemas for Resume Audit Engine.

Conforms to ENGINE_RESUME_AUDIT.md specification.
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ResumeAuditInput(BaseModel):
    """Input schema for Resume Audit Engine"""
    
    # Required fields
    resume_id: str = Field(..., description="Resume identifier in the system")
    resume_text: str = Field(..., min_length=1, description="Extracted text content from resume")
    user_id: str = Field(..., description="User identifier who owns the resume")
    
    # Optional context fields
    target_job_title: Optional[str] = Field(None, description="Target job title for context-aware analysis")
    target_industry: Optional[str] = Field(None, description="Target industry for context-aware analysis")
    target_keywords: Optional[List[str]] = Field(default_factory=list, description="Target keywords to check for")
    
    # Analysis configuration
    analysis_depth: Literal["basic", "standard", "comprehensive"] = Field(
        default="standard",
        description="Depth of analysis to perform"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include improvement recommendations"
    )
    include_ats_compatibility: bool = Field(
        default=True,
        description="Whether to perform ATS compatibility analysis"
    )
    
    # Metadata
    resume_file_type: Optional[str] = Field(None, description="Original file type (pdf, docx, etc.)")
    resume_file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    upload_timestamp: Optional[datetime] = Field(None, description="When resume was uploaded")


class ResumeAuditSignal(BaseModel):
    """Individual signal generated during audit"""
    
    signal_type: Literal[
        "structure_issue",
        "content_issue",
        "keyword_missing",
        "ats_incompatibility",
        "skill_gap",
        "formatting_issue",
        "strength",
        "recommendation"
    ] = Field(..., description="Type of signal")
    
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(
        ...,
        description="Severity level of the signal"
    )
    
    category: str = Field(..., description="Category of the issue/strength")
    message: str = Field(..., description="Human-readable message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional signal details")
    
    # Location information (if applicable)
    section: Optional[str] = Field(None, description="Resume section where issue/strength was found")
    line_number: Optional[int] = Field(None, ge=1, description="Line number if applicable")


class ResumeAuditRecommendations(BaseModel):
    """Structured recommendations for resume improvement"""
    
    priority_actions: List[str] = Field(
        default_factory=list,
        description="High priority actions to take"
    )
    
    quick_fixes: List[str] = Field(
        default_factory=list,
        description="Quick fixes that can be done immediately"
    )
    
    long_term_improvements: List[str] = Field(
        default_factory=list,
        description="Long-term improvement suggestions"
    )
    
    structure_recommendations: List[str] = Field(
        default_factory=list,
        description="Structure improvement suggestions"
    )
    
    content_recommendations: List[str] = Field(
        default_factory=list,
        description="Content improvement suggestions"
    )
    
    keyword_recommendations: List[str] = Field(
        default_factory=list,
        description="Keyword optimization suggestions"
    )
    
    ats_recommendations: Optional[List[str]] = Field(
        None,
        description="ATS compatibility improvement suggestions"
    )


class ResumeAuditOutput(BaseModel):
    """Output schema for Resume Audit Engine"""
    
    # Signal Integrity (Rule 15)
    decision_slot_id: str = Field(..., description="DecisionSlot ID anchoring this signal")
    engine_version: str = Field(..., description="Engine version that generated this output")
    timestamp: datetime = Field(..., description="When the audit was performed")
    
    # Overall Assessment
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall resume quality score (0-100)")
    score_category: Literal["excellent", "good", "fair", "needs_improvement", "poor"] = Field(
        ...,
        description="Categorical assessment of resume quality"
    )
    
    # Component Scores
    structure_score: float = Field(..., ge=0.0, le=100.0, description="Structure and format score")
    content_score: float = Field(..., ge=0.0, le=100.0, description="Content quality score")
    keyword_score: float = Field(..., ge=0.0, le=100.0, description="Keyword optimization score")
    ats_compatibility_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="ATS compatibility score (if analysis was requested)"
    )
    
    # Signal Types (see Signal Types section below)
    signals: List[ResumeAuditSignal] = Field(
        default_factory=list,
        description="List of structured signals generated by the audit"
    )
    
    # Extracted Information
    detected_keywords: List[str] = Field(default_factory=list, description="Keywords detected in resume")
    missing_keywords: List[str] = Field(default_factory=list, description="Important keywords that are missing")
    industry_keywords: List[str] = Field(default_factory=list, description="Industry-specific keywords found")
    
    # Skills Analysis
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills identified")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills identified")
    skill_gaps: List[str] = Field(default_factory=list, description="Recommended skills to add")
    
    # Experience Analysis
    experience_years: int = Field(default=0, ge=0, description="Years of experience detected")
    job_titles: List[str] = Field(default_factory=list, description="Job titles found in resume")
    companies: List[str] = Field(default_factory=list, description="Companies mentioned")
    
    # Education Analysis
    education_level: Optional[str] = Field(None, description="Highest education level detected")
    institutions: List[str] = Field(default_factory=list, description="Educational institutions")
    certifications: List[str] = Field(default_factory=list, description="Certifications found")
    
    # Recommendations (if requested)
    recommendations: Optional[ResumeAuditRecommendations] = Field(
        None,
        description="Improvement recommendations (if include_recommendations=True)"
    )
    
    # Audit Metadata
    processing_time_seconds: float = Field(..., ge=0.0, description="Time taken to process audit")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis (0-1)")
    analysis_depth_used: str = Field(..., description="Actual analysis depth used")

