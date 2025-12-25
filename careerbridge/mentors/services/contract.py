# mentors/services/contract.py

from typing import Dict, List


# ======================================================
# Trust label rules (single source of truth)
# ======================================================
def build_trust_label(review_count: int, is_verified: bool) -> str:
    """
    Build human-readable trust label for mentor cards.

    Priority (high → low):
    1. Verified + enough reviews
    2. High demand
    3. Platform-selected
    4. New mentor (reviewed)
    """
    if is_verified and review_count >= 5:
        return "Verified and trusted by students"

    if review_count >= 10:
        return "Frequently booked mentor"

    if review_count >= 3:
        return "Selected by our platform"

    return "Carefully reviewed by our platform"


# ======================================================
# Mentor API Contract v1
# ======================================================
def build_mentor_contract(data: Dict, *, is_visitor: bool = False, is_detail_view: bool = False) -> Dict:
    """
    Build a stable Mentor API Contract (v1) for frontend.

    Rules:
    - Operates ONLY on serialized dict
    - Never mutates Django model instances
    - Frontend should render only (no business logic)
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
    # Badges (array, ordered, unique)
    # --------------------------------------------------
    badges: List[str] = []

    # system-level badge (ranking / quality)
    legacy_badge = data.get("badge")
    if legacy_badge in {"new", "top_pick", "featured"}:
        badges.append(legacy_badge)

    # verification badge
    if data.get("is_verified"):
        badges.append("verified")

    # de-duplicate while keeping order
    seen = set()
    data["badges"] = [b for b in badges if not (b in seen or seen.add(b))]

    # --------------------------------------------------
    # Trust layer & rating visibility (P0-3)
    # --------------------------------------------------
    review_count = int(data.get("review_count") or 0)
    rating = data.get("rating")
    is_verified = bool(data.get("is_verified"))

    # Detail view: always show rating, even if < 3 reviews
    # List view: hide rating if < 3 reviews
    if is_detail_view:
        # Always show rating on detail page
        data["trust_label"] = None
        try:
            data["rating"] = float(rating) if rating is not None else None
        except Exception:
            data["rating"] = None
    else:
        # List view: existing behavior
        if review_count < 3:
            # hide stars, show trust label
            data["trust_label"] = build_trust_label(review_count, is_verified)
            data["rating"] = None
        else:
            # show stars, hide trust label
            data["trust_label"] = None
            try:
                data["rating"] = float(rating) if rating is not None else None
            except Exception:
                data["rating"] = None

    data["review_count"] = review_count

    # --------------------------------------------------
    # Primary Service: Single Source of Truth (P0-1, P0-2, P0-3)
    # --------------------------------------------------
    # P0-1: Only process primary_service when services data is available
    has_services = bool(data.get("services"))
    primary_service = None
    primary_service_id = data.get("primary_service_id")
    
    # Only resolve primary_service if services are present in data
    if has_services and primary_service_id:
        services = data.get("services") or []
        # Find the primary service from services list
        for service in services:
            if isinstance(service, dict) and service.get("id") == primary_service_id:
                # Check if service is active
                if service.get("is_active") is not False:
                    primary_service = service
                    break
    
    # --------------------------------------------------
    # Pricing layer
    # --------------------------------------------------
    starting_price = data.get("starting_price") or 0
    try:
        starting_price_num = float(starting_price)
    except Exception:
        starting_price_num = 0.0

    # P0-3: Only override price_label when primary_service exists AND has_services is True
    if primary_service is not None and has_services:
        pricing_model = primary_service.get("pricing_model", "hourly")
        if pricing_model == "hourly" and primary_service.get("price_per_hour"):
            try:
                price_val = float(primary_service["price_per_hour"])
                data["price_label"] = f"${int(price_val)}/hour"
                starting_price_num = price_val  # Update for consistency
            except Exception:
                pass
        elif pricing_model == "fixed" and primary_service.get("fixed_price"):
            try:
                price_val = float(primary_service["fixed_price"])
                data["price_label"] = f"${int(price_val)}"
                starting_price_num = price_val
            except Exception:
                pass
        elif pricing_model == "package" and primary_service.get("package_price"):
            try:
                price_val = float(primary_service["package_price"])
                sessions = primary_service.get("package_sessions", 1)
                data["price_label"] = f"${int(price_val)} for {sessions} session{'s' if sessions > 1 else ''}"
                starting_price_num = price_val
            except Exception:
                pass
        # If no price found in primary service, use display_price if available
        if "price_label" not in data or not data.get("price_label"):
            display_price = primary_service.get("display_price")
            if display_price:
                data["price_label"] = display_price
            else:
                # Fallback to starting_price only when we have service data
                data["price_label"] = (
                    f"From ${int(starting_price_num)}" if starting_price_num >= 1 else "From $0"
                )
    elif not has_services:
        # When services are missing: compute price_label from starting_price ONLY if not already provided
        if not data.get("price_label"):
            data["price_label"] = (
                f"From ${int(starting_price_num)}" if starting_price_num >= 1 else "From $0"
            )

    data["starting_price"] = starting_price_num
    data["price_unit"] = "session"

    # --------------------------------------------------
    # CTA layer (UI-safe labels, max 22 chars)
    # --------------------------------------------------
    # P0-3: Only override cta_label when primary_service exists AND has_services is True
    if primary_service is not None and has_services:
        service_title = primary_service.get("title", "")
        service_type = primary_service.get("service_type", "")
        
        # Create CTA from service title (truncate if needed)
        if service_title:
            # Keep first part of title, max 22 chars
            cta_label = service_title[:22] if len(service_title) <= 22 else service_title[:19] + "..."
        elif service_type == "resume_review":
            cta_label = "Resume review"
        elif service_type == "mock_interview":
            cta_label = "Mock interview"
        elif service_type == "career_consultation":
            cta_label = "Career consultation"
        else:
            cta_label = "Book session"
        
        data["cta_label"] = cta_label
    # When services are missing: KEEP serializer-provided cta_label, DO NOT infer from primary_track
    
    data.setdefault("cta_action", "view")
    if "cta_label" not in data:
        # Only set default if serializer didn't provide one
        data["cta_label"] = "Book session"

    # --------------------------------------------------
    # Safe defaults (never let frontend guess)
    # --------------------------------------------------
    data.setdefault("primary_focus", "")
    data.setdefault("session_focus", "")
    data.setdefault("expertise", [])

    # --------------------------------------------------
    # Mentor card display data (P0-2: Service-driven copy ONLY when service exists)
    # --------------------------------------------------
    # P0-2: Only build mentor_card from primary_service when it exists AND has_services is True
    if primary_service is not None and has_services:
        service_title = (primary_service.get("title") or "").strip()
        service_desc = (primary_service.get("description") or "").strip()
        deliverables = primary_service.get("deliverables")

        # --------
        # line1: Service title (never empty if service exists)
        # --------
        line1 = service_title or "Mentor session"

        # --------
        # line2: Outcome-oriented copy (NEVER empty)
        # Priority:
        # 1. Deliverables (non-empty list)
        # 2. Description (non-empty string)
        # 3. Auto-generated fallback
        # --------
        line2 = ""

        if isinstance(deliverables, list) and len(deliverables) > 0:
            line2 = ", ".join(str(d) for d in deliverables[:2])
            if len(deliverables) > 2:
                line2 += "..."
        elif service_desc:
            line2 = (
                service_desc[:100] + "..."
                if len(service_desc) > 100
                else service_desc
            )
        else:
            # SaaS-grade guaranteed fallback (never empty)
            line2 = (
                f"One-on-one {service_title.lower()} with actionable feedback."
                if service_title
                else "One-on-one mentoring session with actionable feedback."
            )

        # --------
        # Mentor Card
        # --------
        data["mentor_card"] = {
            "line1": line1,
            "line2": line2,
        }

        # --------
        # Hero (Detail page single source of truth)
        # --------
        data["hero_title"] = (
            primary_service.get("service_type", "")
            .replace("_", " ")
            .upper()
        )

        data["hero_headline"] = line1
        data["hero_subline"] = line2 # Do NOT set mentor_card fallback when services are missing - leave existing values as-is

    return data
