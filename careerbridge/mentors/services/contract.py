# mentors/services/contract.py

from typing import Dict, List
from datetime import timedelta
from django.utils import timezone

# ======================================================
# Trust label rules (single source of truth)
# ======================================================
def build_trust_label(review_count: int, is_verified: bool) -> str:
    """
    Build human-readable trust label for mentor cards.

    Used ONLY when rating is hidden.
    """
    if is_verified and review_count >= 5:
        return "Verified and trusted by students"

    if review_count >= 10:
        return "Frequently booked mentor"

    if review_count >= 3:
        return "Selected by our platform"

    return "Carefully reviewed by our platform"


def _format_price(value: float) -> str:
    if value % 1:
        return f"${value:.2f}"
    return f"${int(value)}"


# ======================================================
# Mentor API Contract v1 (Single Source of Truth)
# ======================================================
def build_mentor_contract(data: Dict, *, is_detail_view: bool = False) -> Dict:
    """
    Build a stable Mentor API Contract (v1) for frontend.

    Principles:
    - Contract decides semantics (truth), not serializer / queryset
    - Single source of truth for rating / review_count / badges
    - Frontend renders ONLY, never guesses
    """

    # --------------------------------------------------
    # Identity: display_name
    # --------------------------------------------------
    user = data.get("user") or {}
    first = (user.get("first_name") or "").strip()
    last = (user.get("last_name") or "").strip()
    username = (user.get("username") or "").replace("_", " ").strip()

    data["display_name"] = f"{first} {last}".strip() or username or "Mentor"

    # --------------------------------------------------
    # 🔑 Rating & Review Count (Single Source of Truth)
    # --------------------------------------------------
    raw_review_count = (
        data.get("review_count")
        or data.get("review_count_calc")
        or data.get("total_reviews")
        or 0
    )
    try:
        review_count = int(raw_review_count)
    except Exception:
        review_count = 0

    raw_rating = (
        data.get("rating")
        or data.get("avg_rating_calc")
        or data.get("average_rating")
    )
    try:
        rating = float(raw_rating) if raw_rating is not None else None
    except Exception:
        rating = None

    data["review_count"] = review_count
    data["rating"] = rating

    # --------------------------------------------------
    # 🎖 Badge production (max ONE, backend-owned)
    # --------------------------------------------------
    badges: List[str] = []

    status = data.get("status")
    total_sessions = int(data.get("total_sessions") or 0)
    total_reviews = review_count
    approved_at = data.get("approved_at")
    is_verified = bool(data.get("is_verified"))

    # legacy system badge (highest priority)
    legacy_badge = data.get("badge")
    if legacy_badge in {"featured", "top_pick"}:
        badges.append("top_pick")

    # verified badge
    elif is_verified:
        badges.append("verified")

    # new mentor badge (default when review_count < 3)
    else:
        if total_reviews < 3:
            badges.append("new")

    data["badges"] = badges

    # --------------------------------------------------
    # Trust layer & rating visibility
    # --------------------------------------------------
    if is_detail_view:
        # Detail page: always show rating if exists
        data["trust_label"] = None
        data["rating"] = rating
    else:
        # List page: hide rating when insufficient reviews
        if review_count < 3:
            data["rating"] = None
            data["trust_label"] = build_trust_label(review_count, bool(data.get("is_verified")))
        else:
            data["trust_label"] = None
            data["rating"] = rating

    # --------------------------------------------------
    # Primary Service resolution
    # --------------------------------------------------
    has_services = bool(data.get("services"))
    primary_service = None
    primary_service_id = data.get("primary_service_id")

    if has_services and primary_service_id:
        for service in data.get("services") or []:
            if (
                isinstance(service, dict)
                and service.get("id") == primary_service_id
                and service.get("is_active") is not False
            ):
                primary_service = service
                break

    # --------------------------------------------------
    # Pricing layer (single truth)
    # --------------------------------------------------
    starting_price = data.get("starting_price") or 0
    try:
        starting_price_num = float(starting_price)
    except Exception:
        starting_price_num = 0.0

    if primary_service and has_services:
        pricing_model = primary_service.get("pricing_model", "hourly")

        try:
            if pricing_model == "hourly" and primary_service.get("price_per_hour"):
                price_val = float(primary_service["price_per_hour"])
                data["price_label"] = f"{_format_price(price_val)}/hour"
                starting_price_num = price_val

            elif pricing_model == "fixed" and primary_service.get("fixed_price"):
                price_val = float(primary_service["fixed_price"])
                data["price_label"] = _format_price(price_val)
                starting_price_num = price_val

            elif pricing_model == "package" and primary_service.get("package_price"):
                price_val = float(primary_service["package_price"])
                sessions = primary_service.get("package_sessions", 1)
                data["price_label"] = (
                    f"{_format_price(price_val)} for {sessions} session{'s' if sessions > 1 else ''}"
                )
                starting_price_num = price_val
        except Exception:
            pass

    if not data.get("price_label"):
        data["price_label"] = (
            f"From {_format_price(starting_price_num)}"
            if starting_price_num >= 1
            else "From $0"
        )

    data["starting_price"] = starting_price_num
    data["price_unit"] = "session"

    # --------------------------------------------------
    # CTA layer (safe defaults)
    # --------------------------------------------------
    if primary_service and has_services:
        service_title = primary_service.get("title", "").strip()
        service_type = primary_service.get("service_type", "")

        if service_title:
            data["cta_label"] = (
                service_title[:22]
                if len(service_title) <= 22
                else service_title[:19] + "..."
            )
        elif service_type == "resume_review":
            data["cta_label"] = "Resume review"
        elif service_type == "mock_interview":
            data["cta_label"] = "Mock interview"
        elif service_type == "career_consultation":
            data["cta_label"] = "Career consultation"
        else:
            data["cta_label"] = "Book session"

    data.setdefault("cta_label", "Book session")
    data.setdefault("cta_action", "view")

    # --------------------------------------------------
    # Safe defaults (frontend must never guess)
    # --------------------------------------------------
    data.setdefault("primary_focus", "")
    data.setdefault("session_focus", "")
    data.setdefault("expertise", [])

    # --------------------------------------------------
    # Mentor Card copy (service-driven only)
    # --------------------------------------------------
    if primary_service and has_services:
        service_title = (primary_service.get("title") or "").strip()
        service_desc = (primary_service.get("description") or "").strip()
        deliverables = primary_service.get("deliverables")

        line1 = service_title or "Mentor session"

        if isinstance(deliverables, list) and deliverables:
            line2 = ", ".join(str(d) for d in deliverables[:2])
            if len(deliverables) > 2:
                line2 += "..."
        elif service_desc:
            line2 = service_desc[:100] + "..." if len(service_desc) > 100 else service_desc
        else:
            line2 = "One-on-one mentoring session with actionable feedback."

        data["mentor_card"] = {
            "line1": line1,
            "line2": line2,
        }

        # Detail hero
        data["hero_title"] = (
            primary_service.get("service_type", "")
            .replace("_", " ")
            .upper()
        )
        data["hero_headline"] = line1
        data["hero_subline"] = line2

    return data
