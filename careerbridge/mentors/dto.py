from typing import Dict, Any, List
from mentors.models import MentorProfile, MentorService, MentorAvailability, MentorReview
from mentors.serializers import MentorServiceSerializer, MentorAvailabilitySerializer, MentorReviewSerializer


def build_mentor_dto(profile: MentorProfile, include_related: bool = False) -> Dict[str, Any]:
    """
    Unified representation of a Mentor across the entire system.
    Used by Admin, SuperAdmin, Mentor listing, booking, search, and frontend.
    

    CRITICAL DATA CONTRACT:
        mentor.id MUST be MentorProfile.id (NOT User.id)
        This identifier is used as the canonical key for:
        - booking APIs
        - availability (TimeSlot) queries
        - appointment creation
        - mentor profile retrieval
        RULES:
        - mentor_id === MentorProfile.id (always)
        - mentor.user.id === User.id (authentication only)
        - NEVER use user.id as mentor_id for booking or availability operations

        ⚠️ Changing this contract WILL break booking & availability flows.
        ⚠️ Do NOT modify without updating all dependent APIs.


    Args:
        profile: MentorProfile instance
        include_related: If True, includes services, availability, and reviews
    """
    service: MentorService | None = profile.services.filter(is_active=True).first()
    
    # Build user object with safe avatar URL
    def get_avatar_url(user):
        """Safely get avatar URL or return empty string"""
        try:
            if user.avatar and hasattr(user.avatar, 'url') and user.avatar.name:
                return user.avatar.url
            return ""
        except (ValueError, AttributeError):
            return ""
    
    # CRITICAL: User data - user.id MUST be User.id (for auth only, NOT for booking)
    user_data = {
        "id": profile.user.id,  # User.id - for authentication only
        "username": profile.user.username,
        "email": profile.user.email,
        "first_name": getattr(profile.user, 'first_name', ''),
        "last_name": getattr(profile.user, 'last_name', ''),
        "avatar": get_avatar_url(profile.user),
        "avatar_url": get_avatar_url(profile.user),  # Alias for consistency
    }

    # CRITICAL: Top-level id MUST be MentorProfile.id (NOT User.id)
    # This is the single source of truth for booking/availability APIs.
    # Rule: mentor_id === MentorProfile.id (always)
    # Never use user.id as mentor_id for booking operations.
    dto = {
        "id": profile.id,  # MentorProfile.id - used for booking/availability APIs (CRITICAL)
        "username": profile.user.username,
        "email": profile.user.email,
        "user": user_data,  # Contains User.id in user.id field

        # Profile details
        "bio": profile.bio,
        "years_of_experience": profile.years_of_experience,
        "industry": profile.industry,
        "current_position": profile.current_position,
        "specializations": profile.specializations or [],

        # Mentor statistics
        "average_rating": float(profile.average_rating),
        "total_reviews": profile.total_reviews,
        "sessions_completed": profile.total_sessions,
        "total_sessions": profile.total_sessions,
        "total_earnings": float(profile.total_earnings),

        # Verification
        "is_verified": profile.is_verified,
        "verification_badge": profile.verification_badge or "",
        "is_approved": profile.is_approved,

        # Status & metadata
        "status": profile.status,
        "joined_at": profile.created_at.isoformat() if profile.created_at else None,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "ranking_score": float(profile.ranking_score),

        # Pricing details (from first active service)
        "pricing_model": service.pricing_model if service else None,
        "price_per_hour": float(service.price_per_hour) if service and service.price_per_hour else None,
        "fixed_price": float(service.fixed_price) if service and service.fixed_price else None,
        "package_price": float(service.package_price) if service and service.package_price else None,
        "package_sessions": service.package_sessions if service else None,
        "duration_minutes": service.duration_minutes if service else None,
    }
    
    # Include related data if requested (for detail view)
    if include_related:
        # Services
        services = profile.services.filter(is_active=True)
        dto["services"] = MentorServiceSerializer(services, many=True).data
        
        # Availability
        availability = profile.availabilities.filter(is_active=True)
        dto["availability"] = MentorAvailabilitySerializer(availability, many=True).data
        
        # Reviews (limit to 10 most recent)
        reviews = profile.reviews.all()[:10]
        dto["reviews"] = MentorReviewSerializer(reviews, many=True).data
    
    return dto
