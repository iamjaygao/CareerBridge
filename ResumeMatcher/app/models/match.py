"""
Match-related database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Match(Base):
    """Match model for storing resume-job matches"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(255), unique=True, index=True)
    resume_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    job_title = Column(String(255))
    company = Column(String(255))
    
    # Match results
    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    
    # Analysis details
    skills_match = Column(JSON)  # {"python": 0.8, "django": 0.6}
    experience_match = Column(JSON)
    education_match = Column(JSON)
    missing_skills = Column(JSON)
    recommendations = Column(JSON)
    
    # Metadata
    user_id = Column(String(255), index=True)
    source = Column(String(50))  # api, batch, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    feedback = relationship("MatchFeedback", back_populates="match")
    
    # Indexes
    __table_args__ = (
        Index('idx_matches_user_created', 'user_id', 'created_at'),
        Index('idx_matches_score', 'overall_score'),
    )

class MatchFeedback(Base):
    """Feedback model for match accuracy"""
    __tablename__ = "match_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    user_id = Column(String(255), index=True)
    
    # Feedback details
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text)
    accuracy_score = Column(Float)  # How accurate the match was
    helpful_score = Column(Float)   # How helpful the match was
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="feedback")

class ModelPerformance(Base):
    """Model performance tracking"""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # semantic, keyword, hybrid
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Usage statistics
    total_matches = Column(Integer, default=0)
    successful_matches = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_model_performance_version', 'model_version'),
        Index('idx_model_performance_type', 'model_type'),
    ) 