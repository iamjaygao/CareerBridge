"""
OpenAI Service Integration

This module provides integration with OpenAI API for various AI-powered features
including resume analysis, job matching, and content generation.
"""

import logging
import json
from typing import Dict, List, Any, Optional
import openai
from openai import OpenAI

from ..config import config
from ..utils import (
    retry_on_failure, 
    log_api_call, 
    ExternalServiceError, 
    RateLimitError,
    AuthenticationError,
    sanitize_api_key
)

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI API service integration"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not config.openai.api_key:
            logger.warning("OpenAI API key not configured")
            return
        
        try:
            self.client = OpenAI(api_key=config.openai.api_key)
            logger.info(f"OpenAI client initialized with key: {sanitize_api_key(config.openai.api_key)}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ExternalServiceError(f"OpenAI client initialization failed: {e}", "openai")
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("OpenAI", "chat/completions", "POST")
    def analyze_resume(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze resume using OpenAI
        
        Args:
            resume_text: Resume content
            job_description: Optional job description for targeted analysis
        
        Returns:
            Analysis results including score, feedback, and suggestions
        """
        if not self.client:
            raise ExternalServiceError("OpenAI client not initialized", "openai")
        
        # Prepare the analysis prompt
        if job_description:
            prompt = self._create_targeted_analysis_prompt(resume_text, job_description)
        else:
            prompt = self._create_general_analysis_prompt(resume_text)
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst and career advisor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.openai.max_tokens,
                temperature=config.openai.temperature
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            error_text = str(e).lower()
            if "rate" in error_text or "429" in error_text:
                logger.warning("OpenAI rate limit encountered")
                raise RateLimitError("OpenAI rate limit exceeded", "openai")
            if "auth" in error_text or "key" in error_text or "401" in error_text:
                logger.error("OpenAI authentication failed")
                raise AuthenticationError("OpenAI authentication failed", "openai")
            logger.error(f"OpenAI resume analysis failed: {e}")
            raise ExternalServiceError(f"Resume analysis failed: {e}", "openai")
    
    def _create_general_analysis_prompt(self, resume_text: str) -> str:
        """Create prompt for general resume analysis"""
        return f"""
        Please analyze the following resume and provide a comprehensive assessment in JSON format.
        
        Resume:
        {resume_text}
        
        Please provide analysis in the following JSON structure:
        {{
            "overall_score": 85,
            "strengths": ["Strong technical skills", "Good project experience"],
            "weaknesses": ["Limited leadership experience", "Could improve formatting"],
            "suggestions": [
                "Add quantifiable achievements",
                "Include more leadership examples",
                "Improve action verb usage"
            ],
            "ats_compatibility": {{
                "score": 80,
                "issues": ["Missing keywords", "Format issues"],
                "recommendations": ["Add industry keywords", "Use standard formatting"]
            }},
            "skill_analysis": {{
                "technical_skills": ["Python", "Django", "React"],
                "soft_skills": ["Communication", "Teamwork"],
                "missing_skills": ["AWS", "Docker"]
            }},
            "summary": "Overall strong technical background with room for improvement in leadership and formatting."
        }}
        
        Focus on providing actionable feedback and specific suggestions for improvement.
        """
    
    def _create_targeted_analysis_prompt(self, resume_text: str, job_description: str) -> str:
        """Create prompt for job-specific resume analysis"""
        return f"""
        Please analyze the following resume against the specific job description and provide a targeted assessment in JSON format.
        
        Resume:
        {resume_text}
        
        Job Description:
        {job_description}
        
        Please provide analysis in the following JSON structure:
        {{
            "match_score": 85,
            "key_matches": ["Python experience", "Django framework"],
            "missing_requirements": ["AWS experience", "5+ years experience"],
            "strengths": ["Strong technical background", "Relevant project experience"],
            "weaknesses": ["Limited cloud experience", "Less experience than required"],
            "tailoring_suggestions": [
                "Emphasize cloud-related projects",
                "Highlight relevant achievements",
                "Add specific metrics"
            ],
            "keyword_optimization": {{
                "present_keywords": ["Python", "Django", "API"],
                "missing_keywords": ["AWS", "Docker", "Kubernetes"],
                "suggested_additions": ["Cloud computing", "DevOps", "Microservices"]
            }},
            "summary": "Good technical fit but needs emphasis on cloud and DevOps experience."
        }}
        
        Focus on how well the resume matches the specific job requirements and provide targeted improvement suggestions.
        """
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured format"""
        try:
            # Try to extract JSON from the response
            if "{" in analysis_text and "}" in analysis_text:
                start = analysis_text.find("{")
                end = analysis_text.rfind("}") + 1
                json_str = analysis_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback to basic parsing
                return {
                    "analysis": analysis_text,
                    "parsed": False
                }
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI response as JSON: {e}")
            return {
                "analysis": analysis_text,
                "parsed": False,
                "error": "Failed to parse structured response"
            }
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("OpenAI", "chat/completions", "POST")
    def generate_job_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized job recommendations
        
        Args:
            user_profile: User profile with skills, experience, preferences
        
        Returns:
            List of job recommendations
        """
        if not self.client:
            raise ExternalServiceError("OpenAI client not initialized", "openai")
        
        prompt = f"""
        Based on the following user profile, generate 5 personalized job recommendations in JSON format.
        
        User Profile:
        {json.dumps(user_profile, indent=2)}
        
        Please provide recommendations in the following JSON structure:
        {{
            "recommendations": [
                {{
                    "title": "Software Engineer",
                    "company": "Tech Company",
                    "match_score": 90,
                    "reasoning": "Strong match for Python and Django skills",
                    "requirements": ["Python", "Django", "React"],
                    "location": "Remote",
                    "salary_range": "$80k-$120k"
                }}
            ]
        }}
        
        Focus on roles that match the user's skills and experience level.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": "You are a career advisor specializing in job matching."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.openai.max_tokens,
                temperature=config.openai.temperature
            )
            
            recommendations_text = response.choices[0].message.content
            return self._parse_recommendations_response(recommendations_text)
            
        except Exception as e:
            logger.error(f"OpenAI job recommendations failed: {e}")
            raise ExternalServiceError(f"Job recommendations failed: {e}", "openai")
    
    def _parse_recommendations_response(self, recommendations_text: str) -> List[Dict[str, Any]]:
        """Parse job recommendations response"""
        try:
            if "{" in recommendations_text and "}" in recommendations_text:
                start = recommendations_text.find("{")
                end = recommendations_text.rfind("}") + 1
                json_str = recommendations_text[start:end]
                data = json.loads(json_str)
                return data.get("recommendations", [])
            else:
                return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse job recommendations as JSON")
            return []
    
    @retry_on_failure(max_retries=2, delay=1.0)
    @log_api_call("OpenAI", "chat/completions", "POST")
    def generate_interview_questions(self, job_title: str, company: str, resume_text: str) -> List[str]:
        """
        Generate personalized interview questions
        
        Args:
            job_title: Target job title
            company: Target company
            resume_text: Candidate's resume
        
        Returns:
            List of interview questions
        """
        if not self.client:
            raise ExternalServiceError("OpenAI client not initialized", "openai")
        
        prompt = f"""
        Generate 10 personalized interview questions for a {job_title} position at {company}.
        
        Candidate's Resume:
        {resume_text}
        
        Please provide questions in JSON format:
        {{
            "questions": [
                "Tell me about your experience with Python and Django.",
                "How would you handle a challenging technical problem?",
                "Describe a project where you led a team."
            ]
        }}
        
        Focus on questions that relate to the candidate's specific experience and the job requirements.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": "You are an experienced technical interviewer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.openai.max_tokens,
                temperature=config.openai.temperature
            )
            
            questions_text = response.choices[0].message.content
            return self._parse_questions_response(questions_text)
            
        except Exception as e:
            logger.error(f"OpenAI interview questions failed: {e}")
            raise ExternalServiceError(f"Interview questions generation failed: {e}", "openai")
    
    def _parse_questions_response(self, questions_text: str) -> List[str]:
        """Parse interview questions response"""
        try:
            if "{" in questions_text and "}" in questions_text:
                start = questions_text.find("{")
                end = questions_text.rfind("}") + 1
                json_str = questions_text[start:end]
                data = json.loads(json_str)
                return data.get("questions", [])
            else:
                # Fallback: split by lines and extract questions
                lines = questions_text.split('\n')
                questions = []
                for line in lines:
                    line = line.strip()
                    if line and (line.endswith('?') or line.startswith('Tell me') or line.startswith('How')):
                        questions.append(line)
                return questions[:10]  # Limit to 10 questions
        except json.JSONDecodeError:
            logger.warning("Failed to parse interview questions as JSON")
            return []
    
    def check_health(self) -> Dict[str, Any]:
        """Check OpenAI service health"""
        try:
            if not self.client:
                return {
                    "status": "unhealthy",
                    "error": "Client not initialized"
                }
            
            # Simple health check by making a minimal request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "model": config.openai.model,
                "response_time": "normal"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance
openai_service = OpenAIService() 
