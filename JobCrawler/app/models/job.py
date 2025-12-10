"""
Job-related database models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Company(Base):
    """Company model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(255))
    industry = Column(String(100))
    size = Column(String(50))
    founded_year = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="company")

class Location(Base):
    """Location model"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), index=True)
    country = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="location")

class Skill(Base):
    """Skill model"""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    """Job model"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(3), default="USD")
    job_type = Column(String(50))  # full-time, part-time, contract, etc.
    experience_level = Column(String(50))  # entry, mid, senior, etc.
    remote_work = Column(Boolean, default=False)
    source = Column(String(50))  # indeed, linkedin, etc.
    source_url = Column(String(500))
    external_id = Column(String(255), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="jobs")
    location = relationship("Location", back_populates="jobs")
    skills = relationship("JobSkill", back_populates="job")
    
    # Indexes
    __table_args__ = (
        Index('idx_jobs_title_company', 'title', 'company_id'),
        Index('idx_jobs_location', 'location_id'),
        Index('idx_jobs_source', 'source', 'is_active'),
        Index('idx_jobs_external_id', 'external_id', 'source'),
    )

class JobSkill(Base):
    """Job-Skill relationship model"""
    __tablename__ = "job_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    importance = Column(Float, default=1.0)  # Skill importance score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="skills")
    skill = relationship("Skill")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_job_skill_unique', 'job_id', 'skill_id', unique=True),
    ) 