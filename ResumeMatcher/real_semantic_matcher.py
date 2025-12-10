#!/usr/bin/env python3
"""
Real Semantic Matcher using Sentence Transformers
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple
import structlog

logger = structlog.get_logger()

class RealSemanticMatcher:
    """Real semantic matcher using Sentence Transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic matcher
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.is_initialized = False
        
    def initialize(self):
        """Initialize the model"""
        try:
            logger.info("Initializing semantic matcher", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            self.is_initialized = True
            logger.info("Semantic matcher initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize semantic matcher", error=str(e))
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.model:
                del self.model
                self.model = None
            self.is_initialized = False
            logger.info("Semantic matcher cleaned up")
        except Exception as e:
            logger.error("Error during semantic matcher cleanup", error=str(e))
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text using keyword matching
        
        Args:
            text: Input text to extract skills from
            
        Returns:
            List of extracted skills
        """
        # Common technical skills
        common_skills = [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
            # Frameworks
            "django", "flask", "fastapi", "spring", "react", "angular", "vue", "node.js", "express", "laravel", "rails",
            # Databases
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "oracle", "sql server",
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "git", "ci/cd",
            # Data Science & ML
            "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
            # Other Technologies
            "html", "css", "sass", "less", "webpack", "babel", "nginx", "apache", "linux", "unix"
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic matcher not initialized")
        
        try:
            # Encode texts to embeddings
            embeddings = self.model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error("Error calculating semantic similarity", error=str(e))
            return 0.0
    
    def match_resume_to_job(self, resume_text: str, job_description: str) -> Dict:
        """
        Match resume to job description
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            
        Returns:
            Match result with scores and analysis
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic matcher not initialized")
        
        try:
            # Calculate semantic similarity
            semantic_score = self.calculate_semantic_similarity(resume_text, job_description)
            
            # Extract skills from both texts
            resume_skills = self.extract_skills(resume_text)
            job_skills = self.extract_skills(job_description)
            
            # Calculate skill overlap
            matching_skills = set(resume_skills) & set(job_skills)
            missing_skills = set(job_skills) - set(resume_skills)
            
            # Calculate skill match score
            if job_skills:
                skill_match_score = len(matching_skills) / len(job_skills)
            else:
                skill_match_score = 0.0
            
            # Calculate overall score (weighted combination)
            overall_score = 0.7 * semantic_score + 0.3 * skill_match_score
            
            return {
                "semantic_score": semantic_score,
                "skill_match_score": skill_match_score,
                "overall_score": overall_score,
                "matching_skills": list(matching_skills),
                "missing_skills": list(missing_skills),
                "resume_skills": resume_skills,
                "job_skills": job_skills
            }
            
        except Exception as e:
            logger.error("Error in resume-job matching", error=str(e))
            return {
                "semantic_score": 0.0,
                "skill_match_score": 0.0,
                "overall_score": 0.0,
                "matching_skills": [],
                "missing_skills": [],
                "resume_skills": [],
                "job_skills": [],
                "error": str(e)
            }
    
    def batch_match(self, resume_texts: List[str], job_descriptions: List[str]) -> List[Dict]:
        """
        Batch match multiple resumes to job descriptions
        
        Args:
            resume_texts: List of resume texts
            job_descriptions: List of job description texts
            
        Returns:
            List of match results
        """
        if not self.is_initialized:
            raise RuntimeError("Semantic matcher not initialized")
        
        results = []
        
        for i, resume_text in enumerate(resume_texts):
            for j, job_description in enumerate(job_descriptions):
                match_result = self.match_resume_to_job(resume_text, job_description)
                match_result["resume_index"] = i
                match_result["job_index"] = j
                results.append(match_result)
        
        return results

# Global instance
semantic_matcher = RealSemanticMatcher()

def initialize_semantic_matcher():
    """Initialize the global semantic matcher"""
    semantic_matcher.initialize()

def cleanup_semantic_matcher():
    """Cleanup the global semantic matcher"""
    semantic_matcher.cleanup() 