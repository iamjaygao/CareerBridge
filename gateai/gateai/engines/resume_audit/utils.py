"""
Pure utility functions for resume analysis.

Deterministic scoring and parsing functions - no LLM calls, no DB access.
"""

import re
from typing import List, Dict, Tuple, Set
from datetime import datetime


# Common technical skills patterns
TECHNICAL_SKILLS_PATTERNS = [
    r'\b(python|java|javascript|typescript|react|vue|angular|node\.js|django|flask|fastapi)\b',
    r'\b(sql|postgresql|mysql|mongodb|redis|elasticsearch)\b',
    r'\b(aws|azure|gcp|docker|kubernetes|terraform|jenkins|ci/cd)\b',
    r'\b(git|github|gitlab|bitbucket|jira|confluence)\b',
    r'\b(machine learning|ml|ai|deep learning|tensorflow|pytorch)\b',
    r'\b(html|css|sass|less|bootstrap|tailwind)\b',
    r'\b(rest api|graphql|microservices|api design)\b',
    r'\b(linux|unix|bash|shell scripting|powershell)\b',
]

# Common soft skills patterns
SOFT_SKILLS_PATTERNS = [
    r'\b(leadership|teamwork|collaboration|communication|problem solving)\b',
    r'\b(project management|agile|scrum|kanban|time management)\b',
    r'\b(analytical|critical thinking|creativity|adaptability)\b',
    r'\b(presentation|negotiation|customer service|mentoring)\b',
]

# Education level patterns
EDUCATION_PATTERNS = [
    (r'\b(ph\.?d\.?|doctorate|doctor of philosophy)\b', 'PhD'),
    (r'\b(master\'?s?|m\.?s\.?|m\.?a\.?|m\.?b\.?a\.?)\b', 'Masters'),
    (r'\b(bachelor\'?s?|b\.?s\.?|b\.?a\.?|b\.?e\.?)\b', 'Bachelors'),
    (r'\b(associate\'?s?|a\.?a\.?|a\.?s\.?)\b', 'Associates'),
    (r'\b(high school|diploma|ged)\b', 'High School'),
]

# Common resume sections
RESUME_SECTIONS = [
    'contact', 'summary', 'objective', 'experience', 'work experience',
    'employment', 'education', 'skills', 'certifications', 'projects',
    'achievements', 'awards', 'publications', 'languages', 'references'
]


def extract_keywords(text: str, target_keywords: List[str] = None) -> Tuple[List[str], List[str]]:
    """
    Extract keywords from resume text.
    
    Returns:
        Tuple of (detected_keywords, missing_keywords)
    """
    text_lower = text.lower()
    detected = []
    missing = []
    
    if target_keywords:
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                detected.append(keyword)
            else:
                missing.append(keyword)
    
    return detected, missing


def extract_technical_skills(text: str) -> List[str]:
    """Extract technical skills from resume text."""
    text_lower = text.lower()
    skills = set()
    
    for pattern in TECHNICAL_SKILLS_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        skills.update(matches)
    
    return sorted(list(skills))


def extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills from resume text."""
    text_lower = text.lower()
    skills = set()
    
    for pattern in SOFT_SKILLS_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        skills.update(matches)
    
    return sorted(list(skills))


def extract_education_level(text: str) -> str:
    """Extract highest education level from resume text."""
    text_lower = text.lower()
    
    for pattern, level in EDUCATION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return level
    
    return None


def extract_job_titles(text: str) -> List[str]:
    """Extract job titles from resume text."""
    # Simple pattern: look for common job title patterns
    # This is a simplified version - could be enhanced
    titles = []
    
    # Look for patterns like "Software Engineer", "Senior Developer", etc.
    title_patterns = [
        r'\b(senior|junior|lead|principal|staff)\s+\w+\s+(engineer|developer|analyst|manager|director)\b',
        r'\b\w+\s+(engineer|developer|analyst|manager|director|architect|scientist|specialist)\b',
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        titles.extend([m[0] if isinstance(m, tuple) else m for m in matches])
    
    # Deduplicate and return
    return list(set([t.title() for t in titles if len(t.strip()) > 0]))


def extract_companies(text: str) -> List[str]:
    """Extract company names from resume text."""
    # Simple heuristic: look for capitalized words that might be company names
    # This is simplified - real implementation would need more sophisticated NLP
    companies = []
    
    # Look for patterns like "at Company Name" or "Company Name, Inc."
    patterns = [
        r'\bat\s+([A-Z][a-zA-Z\s&]+(?:Inc\.?|LLC|Corp\.?|Ltd\.?)?)',
        r'\b([A-Z][a-zA-Z\s&]+(?:Inc\.?|LLC|Corp\.?|Ltd\.?))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        companies.extend(matches)
    
    # Clean and deduplicate
    cleaned = []
    for company in companies:
        company = company.strip()
        if len(company) > 2 and company not in cleaned:
            cleaned.append(company)
    
    return cleaned[:10]  # Limit to 10 companies


def extract_certifications(text: str) -> List[str]:
    """Extract certifications from resume text."""
    certs = []
    
    # Look for common certification patterns
    cert_patterns = [
        r'\b([A-Z]{2,10}\s+[Cc]ertified|[Cc]ertified\s+[A-Z][a-zA-Z\s]+)\b',
        r'\b([A-Z]{2,10}\s+[Cc]ertification)\b',
        r'\b([A-Z]{2,10}\s+[Pp]rofessional)\b',
    ]
    
    for pattern in cert_patterns:
        matches = re.findall(pattern, text)
        certs.extend(matches)
    
    return list(set([c.strip() for c in certs if len(c.strip()) > 0]))


def extract_institutions(text: str) -> List[str]:
    """Extract educational institutions from resume text."""
    institutions = []
    
    # Look for patterns like "University of X", "X University", "X College"
    patterns = [
        r'\b([A-Z][a-zA-Z\s]+(?:University|College|Institute|School))\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        institutions.extend(matches)
    
    return list(set([i.strip() for i in institutions if len(i.strip()) > 2]))


def calculate_experience_years(text: str) -> int:
    """Calculate years of experience from resume text."""
    # Look for date patterns and calculate duration
    # This is simplified - real implementation would parse dates more carefully
    date_pattern = r'\b(19|20)\d{2}\b'
    dates = re.findall(date_pattern, text)
    
    if len(dates) >= 2:
        try:
            years = [int(d) for d in dates]
            min_year = min(years)
            max_year = max(years)
            return max(0, max_year - min_year)
        except (ValueError, TypeError):
            pass
    
    # Fallback: look for explicit "X years of experience" patterns
    exp_pattern = r'(\d+)\s+years?\s+of\s+experience'
    matches = re.findall(exp_pattern, text, re.IGNORECASE)
    if matches:
        try:
            return int(matches[0])
        except (ValueError, TypeError):
            pass
    
    return 0


def detect_resume_sections(text: str) -> Dict[str, bool]:
    """Detect which resume sections are present."""
    text_lower = text.lower()
    sections_found = {}
    
    for section in RESUME_SECTIONS:
        # Look for section headers
        patterns = [
            rf'\b{section}\b',
            rf'{section}\s*:',
            rf'{section}\s*$',
        ]
        
        found = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns)
        sections_found[section] = found
    
    return sections_found


def calculate_structure_score(text: str) -> float:
    """Calculate structure score (0-100) based on resume structure."""
    sections = detect_resume_sections(text)
    
    # Essential sections
    essential = ['contact', 'experience', 'education']
    essential_found = sum(1 for s in essential if sections.get(s, False))
    essential_score = (essential_found / len(essential)) * 40
    
    # Important sections
    important = ['skills', 'summary']
    important_found = sum(1 for s in important if sections.get(s, False))
    important_score = (important_found / len(important)) * 30
    
    # Optional sections
    optional = ['certifications', 'projects', 'achievements']
    optional_found = sum(1 for s in optional if sections.get(s, False))
    optional_score = min(optional_found / len(optional), 1.0) * 30
    
    return min(100.0, essential_score + important_score + optional_score)


def calculate_content_score(text: str) -> float:
    """Calculate content quality score (0-100)."""
    score = 50.0  # Base score
    
    # Check for quantifiable achievements
    number_pattern = r'\b(\d+%|\d+\s*(?:million|thousand|k|m|years?|months?|people|users|customers))\b'
    if re.search(number_pattern, text, re.IGNORECASE):
        score += 15.0
    
    # Check for action verbs
    action_verbs = ['achieved', 'improved', 'increased', 'developed', 'managed', 'led', 'created', 'implemented']
    verb_count = sum(1 for verb in action_verbs if verb.lower() in text.lower())
    if verb_count >= 3:
        score += 15.0
    elif verb_count >= 1:
        score += 7.5
    
    # Check for technical skills
    tech_skills = extract_technical_skills(text)
    if len(tech_skills) >= 5:
        score += 10.0
    elif len(tech_skills) >= 2:
        score += 5.0
    
    # Check for experience
    exp_years = calculate_experience_years(text)
    if exp_years >= 5:
        score += 10.0
    elif exp_years >= 2:
        score += 5.0
    
    return min(100.0, score)


def calculate_keyword_score(text: str, target_keywords: List[str] = None) -> float:
    """Calculate keyword optimization score (0-100)."""
    if not target_keywords:
        # If no target keywords, score based on keyword density
        words = text.lower().split()
        unique_words = len(set(words))
        total_words = len(words)
        
        if total_words > 0:
            diversity = unique_words / total_words
            return min(100.0, diversity * 100)
        return 50.0
    
    detected, missing = extract_keywords(text, target_keywords)
    
    if len(target_keywords) == 0:
        return 50.0
    
    match_ratio = len(detected) / len(target_keywords)
    return min(100.0, match_ratio * 100)


def calculate_ats_score(text: str) -> float:
    """Calculate ATS compatibility score (0-100)."""
    score = 100.0
    
    # Check for problematic characters
    problematic_chars = ['•', '→', '–', '—', '©', '®', '™']
    for char in problematic_chars:
        if char in text:
            score -= 5.0
    
    # Check for excessive special formatting
    if text.count('\t') > 10:
        score -= 10.0
    
    # Check for reasonable length
    if len(text) < 100:
        score -= 20.0
    elif len(text) > 5000:
        score -= 10.0
    
    # Check for common ATS-friendly patterns
    if re.search(r'\b(email|phone|linkedin)\b', text, re.IGNORECASE):
        score += 5.0
    
    return max(0.0, min(100.0, score))


def calculate_overall_score(structure: float, content: float, keyword: float, ats: float = None) -> float:
    """Calculate overall score from component scores."""
    weights = {
        'structure': 0.25,
        'content': 0.35,
        'keyword': 0.25,
        'ats': 0.15 if ats is not None else 0.0,
    }
    
    # Adjust weights if ATS is not included
    if ats is None:
        total_weight = weights['structure'] + weights['content'] + weights['keyword']
        weights['structure'] /= total_weight
        weights['content'] /= total_weight
        weights['keyword'] /= total_weight
    
    overall = (
        structure * weights['structure'] +
        content * weights['content'] +
        keyword * weights['keyword']
    )
    
    if ats is not None:
        overall += ats * weights['ats']
    
    return round(overall, 2)


def get_score_category(score: float) -> str:
    """Get score category from overall score."""
    if score >= 90:
        return "excellent"
    elif score >= 80:
        return "good"
    elif score >= 70:
        return "fair"
    elif score >= 60:
        return "needs_improvement"
    else:
        return "poor"

