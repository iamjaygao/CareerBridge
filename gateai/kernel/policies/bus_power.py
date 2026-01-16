"""
Bus Power Master Switch Policy

Phase-A: Install bus power control infrastructure (全 OFF 模式)

Purpose:
- Centralized power control for all capability buses
- Phase-A: All buses OFF except KERNEL_CORE_BUS
- Preparation for future capability activation

Constraint:
- Read-only policy (no write interface)
- Default all OFF
- KERNEL_CORE_BUS always ON

Architecture:
Each "bus" represents a logical capability domain.
When a bus is OFF, all requests to that domain return 404.
When a bus is ON, requests proceed to normal governance/routing.

Phase-A State: Installation only, not activation.
"""

# Bus Power Policy (Phase-A: 总闸安装，全 OFF)
# GateAI Capability Constitution - Canonical 8 Buses
BUS_POWER = {
    # Kernel Core Bus (Always ON)
    "KERNEL_CORE_BUS": "ON",
    
    # Public Web Bus (Landing, Marketing) (OFF)
    "PUBLIC_WEB_BUS": "OFF",
    
    # Admin Operations Bus (Staff, Audit, Ops, Console) (OFF)
    "ADMIN_BUS": "OFF",
    
    # AI Capability Bus (ATS, Signals, Engines, Decision Slots) (OFF)
    "AI_BUS": "OFF",
    
    # Peer Mock Runtime Bus (Simulation, Testing) (ON - Phase-A experimental capability)
    "PEER_MOCK_BUS": "ON",
    
    # Mentor/Human Loop Bus (Appointments, Availability) (OFF)
    "MENTOR_BUS": "OFF",
    
    # Payment/Transaction Bus (Stripe, Billing) (OFF)
    "PAYMENT_BUS": "OFF",
    
    # Search/Discovery Bus (Search, Analytics) (OFF)
    "SEARCH_BUS": "OFF",
}


def resolve_bus(path: str) -> str:
    """
    Resolve request path to bus identifier.
    
    GateAI Capability Constitution - Canonical 8 Buses
    
    Phase-A: All non-kernel buses are OFF.
    This function provides the routing logic for future activation.
    
    Args:
        path: HTTP request path
        
    Returns:
        Bus identifier (e.g., "KERNEL_CORE_BUS", "AI_BUS")
        Returns "UNKNOWN" if path doesn't match any known bus
        
    Resolution Rules (Priority Order):
    1. Kernel Core Bus (highest priority)
    2. Peer Mock Runtime Bus (simulation/testing)
    3. AI Capability Bus (engines, signals, decision slots)
    4. Mentor Bus (appointments, human loop, availability)
    5. Payment Bus (stripe, billing, transactions)
    6. Search Bus (search, analytics)
    7. Admin Bus (staff, audit, ops, console)
    8. Public Web Bus (marketing, landing, fallback)
    """
    
    # 1. Kernel Core Bus (Always ON)
    if path.startswith('/kernel/') or path.startswith('/superadmin/'):
        return "KERNEL_CORE_BUS"
    
    # 2. Peer Mock Runtime Bus (simulation, testing, mocking)
    if (path.startswith('/api/v1/peer-mock/') or
        any(keyword in path.lower() for keyword in ['/peer', '/mock', '/simulator', '/runtime-mock'])):
        return "PEER_MOCK_BUS"
    
    # 3. AI Capability Bus (consolidated: AI, ATS, Signals, Engines, Decision Slots, Chat)
    if (path.startswith('/api/v1/ai/') or 
        path.startswith('/api/v1/ats-signals/') or
        path.startswith('/api/v1/signals/') or
        path.startswith('/api/v1/signal-delivery/') or
        path.startswith('/api/v1/decision-slots/') or
        path.startswith('/api/v1/chat/') or
        path.startswith('/api/engines/')):
        return "AI_BUS"
    
    # 4. Mentor Bus (appointments, human loop, availability)
    if (path.startswith('/api/v1/mentors/') or 
        path.startswith('/api/v1/human-loop/') or
        path.startswith('/api/v1/appointments/') or
        path.startswith('/api/v1/availability/')):
        return "MENTOR_BUS"
    
    # 5. Payment Bus (payments, billing, stripe)
    if (path.startswith('/api/v1/payments/') or
        path.startswith('/api/v1/billing/') or
        path.startswith('/api/v1/stripe/')):
        return "PAYMENT_BUS"
    
    # 6. Search Bus (search, analytics)
    if (path.startswith('/api/v1/search/') or
        path.startswith('/api/v1/analytics/')):
        return "SEARCH_BUS"
    
    # 7. Admin Bus (consolidated: admin, staff, audit, ops, console)
    if (path.startswith('/admin/') or
        path.startswith('/staff/') or
        path.startswith('/audit/') or
        path.startswith('/ops/') or
        path.startswith('/console/')):
        return "ADMIN_BUS"
    
    # 8. Public Web Bus (marketing, landing, etc.)
    if path.startswith('/') and not path.startswith('/api/'):
        return "PUBLIC_WEB_BUS"
    
    # Unknown path - don't block (for backward compatibility)
    return "UNKNOWN"


def is_bus_powered(bus: str) -> bool:
    """
    Check if a bus is powered ON.
    
    Args:
        bus: Bus identifier
        
    Returns:
        True if bus is ON, False otherwise
    """
    if bus == "UNKNOWN":
        # Don't block unknown paths (fail-open for compatibility)
        return True
    
    return BUS_POWER.get(bus, "OFF") == "ON"


def get_bus_state(bus: str) -> str:
    """
    Get the power state of a bus.
    
    Args:
        bus: Bus identifier
        
    Returns:
        "ON" or "OFF"
    """
    return BUS_POWER.get(bus, "OFF")


def get_all_buses() -> dict:
    """
    Get all bus power states.
    
    Returns:
        Dict of bus -> state
    """
    return BUS_POWER.copy()
