"""
Matching service for resume-job matching
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
import uuid
import structlog
from datetime import datetime

from app.models.match import Match, MatchFeedback
from app.services.matchers.semantic_matcher import SemanticMatcher
from app.services.matchers.keyword_matcher import KeywordMatcher
from app.core.config import settings

logger = structlog.get_logger()

class MatchingService:
    """Service for handling resume-job matching"""
    
    _semantic_matcher = None
    _keyword_matcher = None
    
    @classmethod
    async def initialize(cls):
        """Initialize matching models"""
        try:
            cls._semantic_matcher = SemanticMatcher()
            cls._keyword_matcher = KeywordMatcher()
            await cls._semantic_matcher.initialize()
            await cls._keyword_matcher.initialize()
            logger.info("Matching service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize matching service", error=str(e))
    
    @classmethod
    async def cleanup(cls):
        """Cleanup matching models"""
        try:
            if cls._semantic_matcher:
                await cls._semantic_matcher.cleanup()
            if cls._keyword_matcher:
                await cls._keyword_matcher.cleanup()
            logger.info("Matching service cleaned up successfully")
        except Exception as e:
            logger.error("Failed to cleanup matching service", error=str(e))
    
    @classmethod
    async def match_resume(
        cls,
        resume_text: str,
        job_description: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        user_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict:
        """Match a resume to a job description"""
        try:
            # Generate match ID
            match_id = str(uuid.uuid4())
            
            # Perform matching using different algorithms
            semantic_score = await cls._semantic_matcher.match(
                resume_text, job_description
            )
            keyword_score = await cls._keyword_matcher.match(
                resume_text, job_description
            )
            
            # Calculate overall score (weighted average)
            overall_score = (semantic_score * 0.7) + (keyword_score * 0.3)
            
            # Generate detailed analysis
            analysis = await cls._generate_analysis(
                resume_text, job_description, semantic_score, keyword_score
            )
            
            # Create match result
            match_result = {
                "match_id": match_id,
                "overall_score": round(overall_score, 3),
                "semantic_score": round(semantic_score, 3),
                "keyword_score": round(keyword_score, 3),
                "analysis": analysis,
                "job_title": job_title,
                "company": company,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store in database if provided
            if db:
                await cls._store_match(match_result, user_id, db)
            
            logger.info("Match completed", match_id=match_id, score=overall_score)
            return match_result
            
        except Exception as e:
            logger.error("Match failed", error=str(e))
            raise
    
    @classmethod
    async def batch_match(
        cls,
        resumes: List[Dict],
        job_descriptions: List[Dict],
        user_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[Dict]:
        """Batch match multiple resumes to job descriptions"""
        results = []
        
        for resume in resumes:
            for job in job_descriptions:
                try:
                    match_result = await cls.match_resume(
                        resume_text=resume["text"],
                        job_description=job["description"],
                        job_title=job.get("title"),
                        company=job.get("company"),
                        user_id=user_id,
                        db=db
                    )
                    results.append(match_result)
                except Exception as e:
                    logger.error("Batch match item failed", error=str(e))
                    continue
        
        return results
    
    @classmethod
    async def get_match(cls, match_id: str, db: AsyncSession) -> Optional[Dict]:
        """Get match by ID"""
        try:
            # Query database for match
            result = await db.execute(
                "SELECT * FROM matches WHERE match_id = :match_id",
                {"match_id": match_id}
            )
            match = result.fetchone()
            
            if not match:
                return None
            
            return dict(match)
        except Exception as e:
            logger.error("Get match failed", match_id=match_id, error=str(e))
            return None
    
    @classmethod
    async def get_match_analysis(cls, match_id: str, db: AsyncSession) -> Optional[Dict]:
        """Get detailed match analysis"""
        try:
            match = await cls.get_match(match_id, db)
            if not match:
                return None
            
            # Return enhanced analysis
            return {
                "match_id": match_id,
                "overall_score": match["overall_score"],
                "detailed_analysis": match.get("analysis", {}),
                "feedback": await cls._get_match_feedback(match_id, db)
            }
        except Exception as e:
            logger.error("Get match analysis failed", match_id=match_id, error=str(e))
            return None
    
    @classmethod
    async def submit_feedback(
        cls,
        match_id: str,
        rating: int,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None,
        db: AsyncSession = None
    ):
        """Submit feedback on match accuracy"""
        try:
            if db:
                feedback = MatchFeedback(
                    match_id=match_id,
                    user_id=user_id,
                    rating=rating,
                    feedback_text=feedback_text
                )
                db.add(feedback)
                await db.commit()
            
            logger.info("Feedback submitted", match_id=match_id, rating=rating)
        except Exception as e:
            logger.error("Submit feedback failed", match_id=match_id, error=str(e))
            raise
    
    @classmethod
    async def _generate_analysis(
        cls,
        resume_text: str,
        job_description: str,
        semantic_score: float,
        keyword_score: float
    ) -> Dict:
        """Generate detailed analysis of the match"""
        # Mock analysis - in real implementation, this would use AI
        return {
            "skills_match": {
                "python": 0.8,
                "django": 0.6,
                "postgresql": 0.9
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
                "Include project management skills"
            ]
        }
    
    @classmethod
    async def _store_match(cls, match_result: Dict, user_id: str, db: AsyncSession):
        """Store match result in database"""
        try:
            match = Match(
                match_id=match_result["match_id"],
                resume_text="",  # Store hash or reference
                job_description="",  # Store hash or reference
                job_title=match_result.get("job_title"),
                company=match_result.get("company"),
                overall_score=match_result["overall_score"],
                skills_score=match_result["analysis"]["skills_match"].get("overall", 0),
                experience_score=match_result["analysis"]["experience_match"].get("relevant_experience", 0),
                education_score=match_result["analysis"]["education_match"].get("field_relevance", 0),
                skills_match=match_result["analysis"]["skills_match"],
                experience_match=match_result["analysis"]["experience_match"],
                education_match=match_result["analysis"]["education_match"],
                missing_skills=match_result["analysis"]["missing_skills"],
                recommendations=match_result["analysis"]["recommendations"],
                user_id=user_id,
                source="api"
            )
            db.add(match)
            await db.commit()
        except Exception as e:
            logger.error("Store match failed", error=str(e))
            await db.rollback()
    
    @classmethod
    async def _get_match_feedback(cls, match_id: str, db: AsyncSession) -> List[Dict]:
        """Get feedback for a match"""
        try:
            result = await db.execute(
                "SELECT * FROM match_feedback WHERE match_id = :match_id",
                {"match_id": match_id}
            )
            feedback = result.fetchall()
            return [dict(f) for f in feedback]
        except Exception as e:
            logger.error("Get match feedback failed", match_id=match_id, error=str(e))
            return [] 