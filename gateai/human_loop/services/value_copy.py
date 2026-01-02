"""
Value Copy Service
------------------
This module generates market-grade value copy for mentor cards.

Rules:
- Operates ONLY on serialized dict (API contract)
- Never mutates Django model instances
- Backend owns product language
- Safe fallbacks for all cases
"""

from typing import Dict


def enrich_mentor_value_copy(data: Dict) -> Dict:
    """
    Enrich serialized mentor data with:
    - primary_focus
    - session_focus
    - cta_label
    - system_insight
    - mentor_card (result-oriented copy)
    """

    # -------------------------
    # Base signals
    # -------------------------
    track = data.get("primary_track")
    review_count = data.get("review_count", 0) or 0
    total_sessions = data.get("total_sessions", 0) or 0
    is_verified = bool(data.get("is_verified", False))

    # -------------------------
    # 1. Primary value copy
    # -------------------------
    if track == "resume_review":
        data.setdefault("primary_focus", "Turn your resume into interviews")
        data.setdefault(
            "session_focus",
            "Actionable feedback tailored to your background",
        )

    elif track == "mock_interview":
        data.setdefault(
            "primary_focus",
            "Ace technical interviews with confidence",
        )
        data.setdefault(
            "session_focus",
            "Mock interviews based on real hiring loops",
        )

    elif track == "career_switch":
        data.setdefault(
            "primary_focus",
            "Break into tech from a non-CS background",
        )
        data.setdefault(
            "session_focus",
            "A clear roadmap based on your experience",
        )

    elif track == "advanced_interview":
        data.setdefault(
            "primary_focus",
            "See if you're ready for senior roles",
        )
        data.setdefault(
            "session_focus",
            "Honest feedback on your current level",
        )

    else:
        # Global safe fallback
        data.setdefault("primary_focus", "Get 1-on-1 career guidance")
        data.setdefault(
            "session_focus",
            "Personalized advice based on your goals",
        )

    # -------------------------
    # 2. System insight (trust layer)
    # -------------------------
    if review_count < 3:
        data["system_insight"] = "New mentor, carefully reviewed"

    elif review_count < 10:
        data["system_insight"] = "Selected by our platform"

    else:
        data["system_insight"] = "Frequently booked mentor"

    if is_verified and review_count >= 5:
        data["system_insight"] = "Verified and trusted by students"

    # -------------------------
    # 3. Mentor card copy (result-oriented messaging)
    # -------------------------
    # Only populate if not already present or empty
    existing_mentor_card = data.get("mentor_card")
    should_populate = (
        not existing_mentor_card
        or not isinstance(existing_mentor_card, dict)
        or not existing_mentor_card.get("line1")
        or not existing_mentor_card.get("line2")
    )
    if should_populate:
        line1 = ""
        line2 = ""

        if track == "resume_review":
            if review_count >= 10:
                line1 = "Not getting interview callbacks?"
                line2 = "Clear, actionable resume feedback"
            elif review_count < 3:
                line1 = "Unsure if your resume works?"
                line2 = "Get honest, first-principles feedback"
            else:
                line1 = "Your resume feels fine, but results aren't?"
                line2 = "Fix the parts recruiters silently reject"

        elif track == "mock_interview":
            if total_sessions >= 30:
                line1 = "Interviews make you freeze?"
                line2 = "Practice real interview pressure"
            elif review_count < 3:
                line1 = "First time doing mock interviews?"
                line2 = "Low-pressure practice, real insights"
            else:
                line1 = "Interview answers sound okay, but not strong?"
                line2 = "Sharpen responses and delivery"

        elif track == "career_switch":
            if review_count >= 5:
                line1 = "Switching careers feels overwhelming?"
                line2 = "A realistic plan based on your background"
            else:
                line1 = "Switching careers but feeling stuck?"
                line2 = "Turn confusion into clear next steps"

        elif track == "advanced_interview":
            if total_sessions >= 20:
                line1 = "Senior interviews feel unpredictable?"
                line2 = "Train system design depth and tradeoffs"
            else:
                line1 = "Aiming for senior or staff roles?"
                line2 = "Know exactly what senior interviews look for"

        else:
            # Fallback: use existing primary_focus/session_focus
            line1 = data.get("primary_focus") or ""
            line2 = data.get("session_focus") or ""

        # Only attach if both lines are non-empty
        if line1 and line2:
            data["mentor_card"] = {
                "line1": line1,
                "line2": line2
            }

    return data
