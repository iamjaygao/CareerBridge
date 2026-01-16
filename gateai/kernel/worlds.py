"""
GateAI 4-World OS Constitution

Defines the formal namespace boundaries for the AI OS:
- PUBLIC: Marketing, landing, unauthenticated access
- APP: User workloads (students, mentors, authenticated app features)
- ADMIN: Userland administration (staff, product operations)
- KERNEL: OS control plane (superuser only, immune to feature flags)

This is an OS-grade separation, not a UI permission change.
"""

from typing import List, Dict


# World namespace definitions
WORLD_NAMESPACES: Dict[str, List[str]] = {
    "public": [
        "/",
        "/api/public",
        "/login",
        "/register",
        "/about",
        "/contact",
        "/pricing",
        "/resources",
        "/mentors",  # Public mentor browsing
        "/assessment",
        "/intelligence",
        "/become-a-mentor",
        "/email-verification",
    ],
    "app": [
        "/app",
        "/api/app",
        "/student",
        "/mentor",
        "/dashboard",
        "/profile",
        "/settings",
        "/appointments",
        "/resumes",
        "/chat",
        "/notifications",
        "/api/v1/users/",  # User operations
        "/api/v1/appointments/",
        "/api/v1/chat/",
        "/api/v1/search/",
        "/api/v1/signal-delivery/",
        "/api/v1/ats-signals/",
    ],
    "admin": [
        "/admin",
        "/staff",
        "/api/admin",
        "/api/v1/adminpanel/",  # General admin operations
        "/analytics",
    ],
    "kernel": [
        "/kernel",
        "/kernel/console",  # Kernel Console (Root Control Plane)
        "/kernel/pulse",    # Kernel Pulse (Phase-A.1 Observability)
        "/superadmin",
        "/api/engines",
        "/api/v1/adminpanel/governance",  # Kernel governance APIs
    ],
}


def resolve_world(path: str) -> str:
    """
    Resolve which world a request path belongs to.
    
    Priority order: kernel > admin > app > public
    
    Args:
        path: The request path (e.g., "/superadmin/governance")
        
    Returns:
        World name: "kernel", "admin", "app", or "public" (default)
    """
    # Normalize path
    if not path:
        return "public"
    
    # Check in priority order: kernel first (most restrictive)
    for world in ["kernel", "admin", "app", "public"]:
        prefixes = WORLD_NAMESPACES.get(world, [])
        for prefix in prefixes:
            if path.startswith(prefix):
                return world
    
    # Default to public for unknown paths
    return "public"


def is_kernel_world(world: str) -> bool:
    """Check if a world is the kernel world"""
    return world == "kernel"


def is_userland_world(world: str) -> bool:
    """Check if a world is userland (public, app, or admin)"""
    return world in ["public", "app", "admin"]


def get_world_description(world: str) -> str:
    """Get human-readable description of a world"""
    descriptions = {
        "public": "Public marketing and unauthenticated access",
        "app": "User workloads (students, mentors, authenticated features)",
        "admin": "Userland administration (staff, product operations)",
        "kernel": "OS control plane (superuser only, immune to feature flags)",
    }
    return descriptions.get(world, "Unknown world")
