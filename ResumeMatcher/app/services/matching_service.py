"""
Matching service for resume-job matching
"""

import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
import uuid
import structlog
from datetime import datetime
from openai import AsyncOpenAI

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
        """Generate detailed gap analysis using GPT-4o-mini."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set, cannot generate analysis")
            return {"error": "OPENAI_API_KEY not configured"}

        client = AsyncOpenAI(api_key=api_key)

        system_prompt = (
            "You are an expert technical recruiter and career coach. "
            "Analyze the resume against the job description and return a JSON object "
            "with EXACTLY this structure — no extra keys, no markdown fences:\n\n"
            "{\n"
            '  "match_score": <integer 0-100>,\n'
            '  "hard_gaps": [\n'
            '    {"issue": "<missing requirement>", "reason": "<why it matters for this JD>"}\n'
            "  ],\n"
            '  "soft_gaps": [\n'
            '    {"issue": "<weakness>", "suggestion": "<specific rewrite or action>"}\n'
            "  ],\n"
            '  "strengths": [\n'
            '    {"point": "<strength>", "why": "<why this JD values it>"}\n'
            "  ],\n"
            '  "recommendations": [\n'
            '    {"action": "<specific actionable step>", "priority": "high|medium|low"}\n'
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- match_score must reflect realistic hiring probability (0=no chance, 100=perfect fit)\n"
            "- hard_gaps: requirements the JD explicitly asks for that are absent from the resume\n"
            "- soft_gaps: things that exist but are weak, vague, or unquantified\n"
            "- strengths: genuine advantages this candidate has for THIS specific role\n"
            "- recommendations: ordered by priority, each action must be specific and executable\n"
            "- Be honest and direct. Do not pad the response."
        )

        user_prompt = (
            f"## RESUME\n{resume_text[:6000]}\n\n"
            f"## JOB DESCRIPTION\n{job_description[:4000]}\n\n"
            f"(Embedding similarity score for context: {round(semantic_score * 100, 1)}%)"
        )

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content
            analysis = json.loads(raw)
            logger.info("GPT-4o-mini analysis completed", match_score=analysis.get("match_score"))
            return analysis

        except Exception as e:
            logger.error("GPT analysis failed", error=str(e))
            return {"error": str(e)}
    
    @classmethod
    async def _store_match(cls, match_result: Dict, user_id: str, db: AsyncSession):
        """Store match result in database"""
        try:
            analysis = match_result.get("analysis", {})
            match = Match(
                match_id=match_result["match_id"],
                resume_text="",
                job_description="",
                job_title=match_result.get("job_title"),
                company=match_result.get("company"),
                overall_score=match_result["overall_score"],
                skills_score=analysis.get("match_score", 0) / 100,
                experience_score=0,
                education_score=0,
                skills_match={"strengths": analysis.get("strengths", [])},
                experience_match={"hard_gaps": analysis.get("hard_gaps", [])},
                education_match={"soft_gaps": analysis.get("soft_gaps", [])},
                missing_skills=[g.get("issue", "") for g in analysis.get("hard_gaps", [])],
                recommendations=[r.get("action", "") for r in analysis.get("recommendations", [])],
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