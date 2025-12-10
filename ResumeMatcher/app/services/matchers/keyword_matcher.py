"""
Keyword-based matching
"""

import re
import structlog
from typing import List, Set

logger = structlog.get_logger()

class KeywordMatcher:
    """Keyword-based matching using TF-IDF and exact matching"""
    
    def __init__(self):
        self.initialized = False
        self.common_skills = {
            "python", "java", "javascript", "react", "node.js", "django", "flask",
            "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
            "aws", "azure", "gcp", "git", "jenkins", "agile", "scrum"
        }
    
    async def initialize(self):
        """Initialize the keyword matcher"""
        try:
            logger.info("Initializing keyword matcher")
            self.initialized = True
            logger.info("Keyword matcher initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize keyword matcher", error=str(e))
            raise
    
    async def match(self, resume_text: str, job_description: str) -> float:
        """Perform keyword matching between resume and job description"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Extract keywords from both texts
            resume_keywords = self._extract_keywords(resume_text.lower())
            job_keywords = self._extract_keywords(job_description.lower())
            
            # Calculate keyword overlap
            overlap = len(resume_keywords.intersection(job_keywords))
            total_job_keywords = len(job_keywords)
            
            if total_job_keywords == 0:
                return 0.0
            
            score = overlap / total_job_keywords
            
            logger.debug("Keyword match completed", score=score, overlap=overlap)
            return min(score, 1.0)
            
        except Exception as e:
            logger.error("Keyword matching failed", error=str(e))
            return 0.0
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - in real implementation, use NLP libraries
        words = re.findall(r'\b\w+\b', text)
        
        # Filter for skills and technical terms
        keywords = set()
        for word in words:
            if len(word) > 2 and word in self.common_skills:
                keywords.add(word)
        
        return keywords
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.initialized = False
            logger.info("Keyword matcher cleaned up")
        except Exception as e:
            logger.error("Failed to cleanup keyword matcher", error=str(e)) 