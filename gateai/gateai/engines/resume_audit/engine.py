"""
Resume Audit Engine Implementation

Conforms to:
- ENGINE_RESUME_AUDIT.md specification
- GateAI OS Contract v1.0.1
- BaseEngine contract
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from pydantic import ValidationError

from gateai.engines.base import BaseEngine
from .schemas import (
    ResumeAuditInput,
    ResumeAuditOutput,
    ResumeAuditSignal,
    ResumeAuditRecommendations,
)
from . import utils


class ResumeAuditEngine(BaseEngine):
    """
    Resume Audit Engine - analyzes resumes and generates structured signals.
    
    Conforms to BaseEngine contract and ENGINE_RESUME_AUDIT.md specification.
    """
    
    # Engine metadata
    ENGINE_VERSION = "1.0.0"
    
    # Schema definitions (Rule 14: AUTOMATED CONTRACT TESTING)
    input_schema = ResumeAuditInput
    output_schema = ResumeAuditOutput
    
    def __init__(self):
        """Initialize the engine."""
        self._last_execution_trace: Dict[str, Any] = {
            'latency_ms': 0,
            'tokens_used': None,
            'model_version': None,
        }
    
    def run(self, raw_input: dict, decision_slot_id: str) -> dict:
        """
        Execute resume audit analysis.
        
        Args:
            raw_input: Raw input dictionary (validated against input_schema)
            decision_slot_id: DecisionSlot ID to anchor output (Rule 15: SIGNAL INTEGRITY)
            
        Returns:
            dict: Output dictionary conforming to ResumeAuditOutput schema
            
        Raises:
            ValidationError: If input doesn't conform to input_schema
            ValueError: If decision_slot_id is invalid
        """
        start_time = time.time()
        
        # Validate decision_slot_id (Rule 15)
        if not decision_slot_id or not isinstance(decision_slot_id, str) or len(decision_slot_id.strip()) == 0:
            raise ValueError("Invalid decision_slot_id: must be non-empty string")
        
        # Validate input against schema (Rule 14)
        try:
            validated_input = self.input_schema(**raw_input)
        except ValidationError as e:
            raise ValidationError(f"Input validation failed: {e}")
        
        # Perform analysis
        try:
            output = self._perform_audit(validated_input, decision_slot_id)
            
            # Validate output against schema (Rule 14)
            self.output_schema(**output)
            
            # Store execution trace
            processing_time = time.time() - start_time
            self._last_execution_trace = {
                'latency_ms': int(processing_time * 1000),
                'tokens_used': None,  # No LLM calls
                'model_version': None,  # No LLM calls
            }
            
            return output
            
        except Exception as e:
            # Store error in trace
            processing_time = time.time() - start_time
            self._last_execution_trace = {
                'latency_ms': int(processing_time * 1000),
                'tokens_used': None,
                'model_version': None,
            }
            raise
    
    def _perform_audit(self, input_data: ResumeAuditInput, decision_slot_id: str) -> dict:
        """
        Perform the actual audit analysis.
        
        Args:
            input_data: Validated input data
            decision_slot_id: DecisionSlot ID for anchoring
            
        Returns:
            dict: Output dictionary
        """
        start_time = time.time()
        text = input_data.resume_text
        
        # Calculate component scores
        structure_score = utils.calculate_structure_score(text)
        content_score = utils.calculate_content_score(text)
        keyword_score = utils.calculate_keyword_score(text, input_data.target_keywords)
        ats_score = None
        
        if input_data.include_ats_compatibility:
            ats_score = utils.calculate_ats_score(text)
        
        # Calculate overall score
        overall_score = utils.calculate_overall_score(
            structure_score, content_score, keyword_score, ats_score
        )
        score_category = utils.get_score_category(overall_score)
        
        # Extract information
        detected_keywords, missing_keywords = utils.extract_keywords(text, input_data.target_keywords)
        technical_skills = utils.extract_technical_skills(text)
        soft_skills = utils.extract_soft_skills(text)
        job_titles = utils.extract_job_titles(text)
        companies = utils.extract_companies(text)
        experience_years = utils.calculate_experience_years(text)
        education_level = utils.extract_education_level(text)
        institutions = utils.extract_institutions(text)
        certifications = utils.extract_certifications(text)
        
        # Generate signals
        signals = self._generate_signals(
            input_data,
            structure_score,
            content_score,
            keyword_score,
            ats_score,
            detected_keywords,
            missing_keywords,
            technical_skills,
            soft_skills,
        )
        
        # Generate recommendations if requested
        recommendations = None
        if input_data.include_recommendations:
            recommendations = self._generate_recommendations(
                signals,
                missing_keywords,
                [],
                structure_score,
                content_score,
                keyword_score,
                ats_score,
            )
        
        # Build output
        output = {
            'decision_slot_id': decision_slot_id,  # Rule 15: SIGNAL INTEGRITY
            'engine_version': self.ENGINE_VERSION,
            'timestamp': datetime.utcnow(),
            'overall_score': overall_score,
            'score_category': score_category,
            'structure_score': round(structure_score, 2),
            'content_score': round(content_score, 2),
            'keyword_score': round(keyword_score, 2),
            'ats_compatibility_score': round(ats_score, 2) if ats_score is not None else None,
            'signals': [s.dict() for s in signals],
            'detected_keywords': detected_keywords,
            'missing_keywords': missing_keywords,
            'industry_keywords': [],  # Could be enhanced with industry detection
            'technical_skills': technical_skills,
            'soft_skills': soft_skills,
            'skill_gaps': [],  # Could be enhanced with target role comparison
            'experience_years': experience_years,
            'job_titles': job_titles,
            'companies': companies,
            'education_level': education_level,
            'institutions': institutions,
            'certifications': certifications,
            'recommendations': recommendations.dict() if recommendations else None,
            'processing_time_seconds': round(time.time() - start_time, 3),
            'confidence_score': 0.85,  # Deterministic analysis confidence
            'analysis_depth_used': input_data.analysis_depth,
        }
        
        return output
    
    def _generate_signals(
        self,
        input_data: ResumeAuditInput,
        structure_score: float,
        content_score: float,
        keyword_score: float,
        ats_score: float,
        detected_keywords: List[str],
        missing_keywords: List[str],
        technical_skills: List[str],
        soft_skills: List[str],
    ) -> List[ResumeAuditSignal]:
        """Generate structured signals based on analysis."""
        signals = []
        text = input_data.resume_text.lower()
        
        # Structure signals
        sections = utils.detect_resume_sections(input_data.resume_text)
        if not sections.get('contact', False):
            signals.append(ResumeAuditSignal(
                signal_type='structure_issue',
                severity='critical',
                category='Missing Section',
                message='Contact information section is missing',
                section='contact',
            ))
        
        if not sections.get('experience', False):
            signals.append(ResumeAuditSignal(
                signal_type='structure_issue',
                severity='critical',
                category='Missing Section',
                message='Work experience section is missing',
                section='experience',
            ))
        
        if structure_score < 60:
            signals.append(ResumeAuditSignal(
                signal_type='structure_issue',
                severity='high',
                category='Structure Quality',
                message='Resume structure needs improvement',
                details={'structure_score': structure_score},
            ))
        
        # Content signals
        if content_score < 60:
            signals.append(ResumeAuditSignal(
                signal_type='content_issue',
                severity='high',
                category='Content Quality',
                message='Resume content quality needs improvement',
                details={'content_score': content_score},
            ))
        
        # Check for quantifiable achievements
        if not any(char.isdigit() for char in input_data.resume_text):
            signals.append(ResumeAuditSignal(
                signal_type='content_issue',
                severity='medium',
                category='Achievements',
                message='Resume lacks quantifiable achievements',
            ))
        
        # Keyword signals
        if missing_keywords:
            severity = 'critical' if len(missing_keywords) > 5 else 'high' if len(missing_keywords) > 2 else 'medium'
            signals.append(ResumeAuditSignal(
                signal_type='keyword_missing',
                severity=severity,
                category='Keywords',
                message=f'Missing {len(missing_keywords)} target keywords',
                details={'missing_keywords': missing_keywords[:10]},  # Limit details
            ))
        
        if keyword_score < 50:
            signals.append(ResumeAuditSignal(
                signal_type='keyword_missing',
                severity='high',
                category='Keyword Optimization',
                message='Resume keyword optimization is low',
                details={'keyword_score': keyword_score},
            ))
        
        # ATS signals
        if ats_score is not None and ats_score < 70:
            signals.append(ResumeAuditSignal(
                signal_type='ats_incompatibility',
                severity='high' if ats_score < 50 else 'medium',
                category='ATS Compatibility',
                message='Resume may have ATS compatibility issues',
                details={'ats_score': ats_score},
            ))
        
        # Skill signals
        if technical_skills:
            signals.append(ResumeAuditSignal(
                signal_type='strength',
                severity='info',
                category='Technical Skills',
                message=f'Resume includes {len(technical_skills)} technical skills',
                details={'skills': technical_skills[:5]},
            ))
        
        if soft_skills:
            signals.append(ResumeAuditSignal(
                signal_type='strength',
                severity='info',
                category='Soft Skills',
                message=f'Resume includes {len(soft_skills)} soft skills',
            ))
        
        # Formatting signals (simplified)
        if len(input_data.resume_text) < 200:
            signals.append(ResumeAuditSignal(
                signal_type='content_issue',
                severity='high',
                category='Content Length',
                message='Resume content is too short',
            ))
        
        return signals
    
    def _generate_recommendations(
        self,
        signals: List[ResumeAuditSignal],
        missing_keywords: List[str],
        skill_gaps: List[str],
        structure_score: float,
        content_score: float,
        keyword_score: float,
        ats_score: float,
    ) -> ResumeAuditRecommendations:
        """Generate improvement recommendations."""
        priority_actions = []
        quick_fixes = []
        long_term_improvements = []
        structure_recommendations = []
        content_recommendations = []
        keyword_recommendations = []
        ats_recommendations = []
        
        # Priority actions based on critical signals
        critical_signals = [s for s in signals if s.severity == 'critical']
        if critical_signals:
            priority_actions.append('Address critical issues identified in the audit')
        
        # Structure recommendations
        if structure_score < 70:
            structure_recommendations.append('Ensure all essential sections are present (contact, experience, education)')
            structure_recommendations.append('Add a professional summary or objective section')
            quick_fixes.append('Add missing resume sections')
        
        # Content recommendations
        if content_score < 70:
            content_recommendations.append('Add quantifiable achievements to work experience')
            content_recommendations.append('Use strong action verbs in job descriptions')
            content_recommendations.append('Provide specific examples of accomplishments')
        
        # Keyword recommendations
        if missing_keywords:
            keyword_recommendations.append(f'Add missing keywords: {", ".join(missing_keywords[:5])}')
            quick_fixes.append('Incorporate target keywords naturally into resume content')
        
        if keyword_score < 70:
            keyword_recommendations.append('Optimize resume for target job keywords')
            keyword_recommendations.append('Include industry-standard terminology')
        
        # ATS recommendations
        if ats_score is not None and ats_score < 70:
            ats_recommendations.append('Use standard fonts and formatting')
            ats_recommendations.append('Avoid complex tables and graphics')
            ats_recommendations.append('Use simple, clean formatting')
            quick_fixes.append('Simplify resume formatting for ATS compatibility')
        
        # Long-term improvements
        if content_score < 80:
            long_term_improvements.append('Gain more relevant work experience')
            long_term_improvements.append('Obtain relevant certifications')
        
        return ResumeAuditRecommendations(
            priority_actions=priority_actions,
            quick_fixes=quick_fixes,
            long_term_improvements=long_term_improvements,
            structure_recommendations=structure_recommendations,
            content_recommendations=content_recommendations,
            keyword_recommendations=keyword_recommendations,
            ats_recommendations=ats_recommendations if ats_recommendations else None,
        )
    
    def fallback_logic(self, error: Exception, raw_input: dict, decision_slot_id: str) -> dict:
        """
        Resilience mechanism - return minimal valid output on error.
        
        Rule 7: Resilience (fallback_logic required)
        Rule 15: SIGNAL INTEGRITY - must anchor to decision_slot_id
        """
        error_signal = ResumeAuditSignal(
            signal_type='structure_issue',
            severity='critical',
            category='Processing Error',
            message=f'Resume audit failed: {str(error)}',
            details={
                'error_type': error.__class__.__name__,
                'error_message': str(error),
            },
        )
        
        output = {
            'decision_slot_id': decision_slot_id,  # Rule 15: SIGNAL INTEGRITY
            'engine_version': self.ENGINE_VERSION,
            'timestamp': datetime.utcnow(),
            'overall_score': 0.0,
            'score_category': 'poor',
            'structure_score': 0.0,
            'content_score': 0.0,
            'keyword_score': 0.0,
            'ats_compatibility_score': None,
            'signals': [error_signal.dict()],
            'detected_keywords': [],
            'missing_keywords': [],
            'industry_keywords': [],
            'technical_skills': [],
            'soft_skills': [],
            'skill_gaps': [],
            'experience_years': 0,
            'job_titles': [],
            'companies': [],
            'education_level': None,
            'institutions': [],
            'certifications': [],
            'recommendations': None,
            'processing_time_seconds': 0.0,
            'confidence_score': 0.0,
            'analysis_depth_used': 'basic',
        }
        
        # Validate output
        try:
            self.output_schema(**output)
        except ValidationError as e:
            # If validation fails, we have a serious problem
            raise ValueError(f"Fallback output validation failed: {e}")
        
        return output
    
    def trace_metadata(self) -> Dict[str, Any]:
        """
        Return traceability metadata for the last execution.
        
        Rule 9: Cost Awareness
        Rule 10: Traceability
        """
        return {
            'latency_ms': self._last_execution_trace.get('latency_ms', 0),
            'tokens_used': self._last_execution_trace.get('tokens_used'),
            'model_version': self._last_execution_trace.get('model_version'),
        }

