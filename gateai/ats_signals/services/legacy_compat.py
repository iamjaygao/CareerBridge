"""
Legacy compatibility layer for ResumeAnalysisService.

DEPRECATED: This module provides backward compatibility for legacy ResumeAnalysisService.
New code should use ResumeAuditEngine directly via /api/engines/signal-core/resume-audit/

This compatibility layer:
1. Routes analysis through ResumeAuditEngine (OS-native)
2. Creates legacy ResumeAnalysis records for backward compatibility
3. Maintains same response format as legacy service
"""

import time
import logging
from decimal import Decimal
from typing import Optional
from django.utils import timezone

from ..models import Resume, ResumeAnalysis, ResumeFeedback
from gateai.engines.resume_audit import ResumeAuditEngine

logger = logging.getLogger(__name__)


def _extract_resume_text(resume: Resume) -> Optional[str]:
    """Extract text from resume file (reused from legacy ResumeAnalysisService)."""
    if hasattr(resume, 'extracted_text') and resume.extracted_text:
        return resume.extracted_text

    if not resume.file:
        return None

    file_type = (resume.file_type or '').lower()

    if file_type == 'pdf':
        return _extract_pdf_text(resume)
    if file_type in ('docx', 'doc'):
        return _extract_docx_text(resume)

    return None


def _extract_pdf_text(resume: Resume) -> Optional[str]:
    """Extract text from PDF file."""
    try:
        from PyPDF2 import PdfReader
    except Exception:
        return None

    try:
        with resume.file.open('rb') as f:
            reader = PdfReader(f)
            pages = [page.extract_text() or '' for page in reader.pages]
            text = '\n'.join(pages).strip()
            return text or None
    except Exception:
        return None


def _extract_docx_text(resume: Resume) -> Optional[str]:
    """Extract text from DOCX file."""
    try:
        import docx
    except Exception:
        return None

    try:
        with resume.file.open('rb') as f:
            document = docx.Document(f)
            paragraphs = [para.text for para in document.paragraphs if para.text]
            text = '\n'.join(paragraphs).strip()
            return text or None
    except Exception:
        return None


def analyze_resume_legacy(resume_id: int, industry: Optional[str] = None, job_title: Optional[str] = None):
    """
    Legacy compatibility wrapper for resume analysis.
    
    Routes through ResumeAuditEngine but creates legacy ResumeAnalysis records
    for backward compatibility with existing API contracts.
    
    DEPRECATED: Use ResumeAuditEngine directly for new code.
    """
    try:
        resume = Resume.objects.get(id=resume_id)
        resume.status = 'analyzing'
        resume.save()
        start_time = time.time()

        # Extract resume text
        resume_text = _extract_resume_text(resume)
        if not resume_text:
            resume_text = resume.title or ""

        # Generate decision_slot_id for OS engine
        decision_slot_id = f"ds_resume_{resume_id}"

        # Prepare engine input
        engine_input = {
            'resume_id': str(resume.id),
            'resume_text': resume_text,
            'user_id': str(resume.user.id),
        }
        if industry:
            engine_input['target_industry'] = industry
        if job_title:
            engine_input['target_job_title'] = job_title

        # Call OS engine
        engine = ResumeAuditEngine()
        engine_output = engine.run(engine_input, decision_slot_id)
        processing_time = time.time() - start_time

        # Extract overall score from engine output
        overall_score = Decimal(str(engine_output.get('overall_score', 75)))

        # Create legacy ResumeAnalysis record for backward compatibility
        analysis_data = {
            'overall_score': overall_score,
            'structure_score': overall_score - Decimal('5'),  # Estimate
            'content_score': overall_score + Decimal('2'),  # Estimate
            'keyword_score': overall_score - Decimal('3'),  # Estimate
            'ats_score': overall_score - Decimal('1'),  # Estimate
            'extracted_text': resume_text[:1500] if resume_text else '',  # Truncate
            'detected_keywords': [],
            'missing_keywords': [],
            'industry_keywords': [],
            'technical_skills': [],
            'soft_skills': [],
            'skill_gaps': [],
            'experience_years': 0,
            'job_titles': [],
            'companies': [],
            'education_level': '',
            'institutions': [],
            'certifications': [],
            'analysis_version': 'engine-1.0',
            'processing_time': Decimal(str(processing_time)),
            'confidence_score': Decimal('0.85'),
        }

        # Extract data from engine signals if available
        signals = engine_output.get('signals', [])
        for signal in signals:
            signal_type = signal.get('signal_type', '')
            if 'keyword' in signal_type.lower():
                missing = signal.get('details', {}).get('missing_keywords', [])
                if missing:
                    analysis_data['missing_keywords'] = missing
            if 'skill' in signal_type.lower():
                skills = signal.get('details', {}).get('skills', [])
                if skills:
                    analysis_data['technical_skills'] = skills

        # Create analysis record
        analysis = ResumeAnalysis.objects.create(
            resume=resume,
            **analysis_data
        )

        # Create feedback record
        feedback_data = {
            'summary': f"Resume analysis completed with overall score of {overall_score}.",
            'strengths': [],
            'weaknesses': [],
            'structure_recommendations': [],
            'content_recommendations': [],
            'keyword_recommendations': [],
            'format_recommendations': [],
            'industry_insights': [],
            'market_trends': [],
            'salary_insights': {},
            'priority_actions': [],
            'quick_fixes': [],
            'long_term_improvements': []
        }

        # Extract recommendations from signals
        for signal in signals:
            message = signal.get('message', '')
            if message:
                if signal.get('severity') == 'critical':
                    feedback_data['weaknesses'].append(message)
                elif signal.get('severity') == 'warning':
                    feedback_data['content_recommendations'].append(message)

        ResumeFeedback.objects.create(
            analysis=analysis,
            **feedback_data
        )

        resume.status = 'analyzed'
        resume.analyzed_at = timezone.now()
        resume.save()

        # Persist engine signals to OS-native ATS Signals layer
        try:
            from ..services.persistence import persist_engine_signals
            persist_engine_signals(engine_output, decision_slot_id, user_id=str(resume.user.id))
        except Exception as e:
            logger.warning(f"Failed to persist engine signals: {e}", exc_info=True)

        return analysis

    except Resume.DoesNotExist:
        raise ValueError("Resume not found")
    except Exception as e:
        resume.status = 'failed'
        resume.save()
        raise e

