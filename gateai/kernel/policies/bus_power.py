"""
Bus Power Master Switch Policy

Phase-A: Bus states are now stored in DB (BusPowerState model).
Only SuperAdmin can modify via /kernel/console/buses/.

Falls back to hardcoded defaults when DB is unavailable (startup safety).
"""

import logging

logger = logging.getLogger(__name__)

# ── Hardcoded defaults (used as seed data and DB-unavailable fallback) ────────
BUS_POWER_DEFAULTS = {
    "KERNEL_CORE_BUS": "ON",
    "PUBLIC_WEB_BUS":  "OFF",
    "ADMIN_BUS":       "OFF",
    "AI_BUS":          "OFF",
    "PEER_MOCK_BUS":   "OFF",  # off until the peer mock feature launches
    "MENTOR_BUS":      "OFF",
    "PAYMENT_BUS":     "OFF",
    "CHAT_BUS":        "OFF",
    "SEARCH_BUS":      "OFF",
}

# Keep BUS_POWER as alias so existing imports don't break
BUS_POWER = BUS_POWER_DEFAULTS

def _load_from_db() -> dict | None:
    """
    Load bus states from BusPowerState table.
    Returns None if DB is not ready (e.g. during startup before migrations).
    """
    try:
        from kernel.governance.models import BusPowerState
        rows = BusPowerState.objects.values("bus_name", "state")
        if not rows:
            return None
        return {r["bus_name"]: r["state"] for r in rows}
    except Exception:
        return None


def _seed_db_if_empty() -> None:
    """
    Seed BusPowerState with hardcoded defaults on first run.
    Safe to call multiple times (noop when records already exist).
    """
    try:
        from kernel.governance.models import BusPowerState
        if BusPowerState.objects.exists():
            return
        BusPowerState.objects.bulk_create([
            BusPowerState(bus_name=bus, state=state)
            for bus, state in BUS_POWER_DEFAULTS.items()
        ])
        logger.info("BusPowerState seeded with defaults")
    except Exception as e:
        logger.warning("Could not seed BusPowerState: %s", e)


def _get_bus_states() -> dict:
    """
    Return current bus states, read from the DB on every call.

    Not cached in-process: the DB row is the only state shared by all
    workers, so a toggle is visible to the very next request everywhere.
    It is one query over at most 8 rows.
    Falls back to hardcoded defaults if DB is unavailable.
    """
    states = _load_from_db()
    if states is None:
        _seed_db_if_empty()
        states = _load_from_db()

    if states:
        return states

    # DB not ready — use hardcoded defaults
    return BUS_POWER_DEFAULTS


def invalidate_cache() -> None:
    """No-op, kept for callers: bus states are no longer cached."""


def resolve_bus(path: str) -> str:
    """
    Resolve request path to bus identifier.

    Resolution Rules (Priority Order):
    1. Kernel Core Bus  (highest priority)
    2. Peer Mock Runtime Bus
    3. AI Capability Bus
    4. Mentor Bus
    5. Payment Bus
    6. Search Bus
    7. Admin Bus
    8. Public Web Bus
    """
    # Kernel core: kernel API, governance, and identity (signup/login/profile).
    # KERNEL_CORE_BUS cannot be switched off.
    if (path.startswith("/kernel/") or
            path.startswith("/superadmin/") or
            path.startswith("/api/v1/kernel/") or
            path.startswith("/api/v1/adminpanel/governance/") or
            path.startswith("/api/v1/users/") or
            path == "/health/" or  # load balancer / Docker healthcheck: never switched off
            path == "/metrics/"):  # Prometheus scrape (token-protected)
        return "KERNEL_CORE_BUS"

    if (path.startswith("/api/v1/peer-mock/") or
            any(k in path.lower() for k in ["/peer", "/mock", "/simulator", "/runtime-mock"])):
        return "PEER_MOCK_BUS"

    if path.startswith("/api/v1/chat/") or path.startswith("/ws/chat/"):
        return "CHAT_BUS"

    # Booking belongs to the mentor module (not AI).
    if path.startswith("/api/v1/decision-slots/"):
        return "MENTOR_BUS"

    if (path.startswith("/api/v1/ai/") or
            path.startswith("/api/v1/ats-signals/") or
            path.startswith("/api/v1/signals/") or
            path.startswith("/api/v1/signal-delivery/") or
            path.startswith("/api/engines/")):
        return "AI_BUS"

    if (path.startswith("/api/v1/mentors/") or
            path.startswith("/api/v1/human-loop/") or
            path.startswith("/api/v1/appointments/") or
            path.startswith("/api/v1/availability/")):
        return "MENTOR_BUS"

    if (path.startswith("/api/v1/payments/") or
            path.startswith("/api/v1/billing/") or
            path.startswith("/api/v1/stripe/")):
        return "PAYMENT_BUS"

    if (path.startswith("/api/v1/search/") or
            path.startswith("/api/v1/analytics/")):
        return "SEARCH_BUS"

    if (path.startswith("/admin/") or
            path.startswith("/api/v1/adminpanel/") or
            path.startswith("/staff/") or
            path.startswith("/audit/") or
            path.startswith("/ops/") or
            path.startswith("/console/")):
        return "ADMIN_BUS"

    if path.startswith("/") and not path.startswith("/api/"):
        return "PUBLIC_WEB_BUS"

    # Public API utility endpoints (index, ping, info)
    if path in ("/api/v1/", "/api/v1/ping/", "/api/info/"):
        return "PUBLIC_WEB_BUS"

    return "UNKNOWN"


def is_bus_powered(bus: str) -> bool:
    # A path with no bus is refused (default deny).
    if bus == "UNKNOWN":
        return False
    return _get_bus_states().get(bus, "OFF") == "ON"


def get_bus_state(bus: str) -> str:
    return _get_bus_states().get(bus, "OFF")


def get_all_buses() -> dict:
    return _get_bus_states().copy()
