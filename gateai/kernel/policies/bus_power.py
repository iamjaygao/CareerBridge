"""
Bus Power Master Switch Policy

Phase-A: Bus states are now stored in DB (BusPowerState model).
Only SuperAdmin can modify via /kernel/console/buses/.

Falls back to hardcoded defaults when DB is unavailable (startup safety).
"""

import time
import logging

logger = logging.getLogger(__name__)

# ── Hardcoded defaults (used as seed data and DB-unavailable fallback) ────────
BUS_POWER_DEFAULTS = {
    "KERNEL_CORE_BUS": "ON",
    "PUBLIC_WEB_BUS":  "OFF",
    "ADMIN_BUS":       "OFF",
    "AI_BUS":          "OFF",
    "PEER_MOCK_BUS":   "ON",
    "MENTOR_BUS":      "OFF",
    "PAYMENT_BUS":     "OFF",
    "SEARCH_BUS":      "OFF",
}

# Keep BUS_POWER as alias so existing imports don't break
BUS_POWER = BUS_POWER_DEFAULTS

# ── In-process cache ──────────────────────────────────────────────────────────
_cache: dict = {}
_cache_ts: float = 0.0
_CACHE_TTL: int = 5  # seconds


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
    Return current bus states with 5-second in-process cache.
    Falls back to hardcoded defaults if DB is unavailable.
    """
    global _cache, _cache_ts

    now = time.time()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache

    _seed_db_if_empty()
    states = _load_from_db()

    if states:
        _cache = states
        _cache_ts = now
        return states

    # DB not ready — use hardcoded defaults (don't cache so we retry next request)
    return BUS_POWER_DEFAULTS


def invalidate_cache() -> None:
    """Force next request to re-read from DB (call after any bus state change)."""
    global _cache, _cache_ts
    _cache = {}
    _cache_ts = 0.0


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
    if path.startswith("/kernel/") or path.startswith("/superadmin/"):
        return "KERNEL_CORE_BUS"

    if (path.startswith("/api/v1/peer-mock/") or
            any(k in path.lower() for k in ["/peer", "/mock", "/simulator", "/runtime-mock"])):
        return "PEER_MOCK_BUS"

    if (path.startswith("/api/v1/ai/") or
            path.startswith("/api/v1/ats-signals/") or
            path.startswith("/api/v1/signals/") or
            path.startswith("/api/v1/signal-delivery/") or
            path.startswith("/api/v1/decision-slots/") or
            path.startswith("/api/v1/chat/") or
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
            path.startswith("/staff/") or
            path.startswith("/audit/") or
            path.startswith("/ops/") or
            path.startswith("/console/")):
        return "ADMIN_BUS"

    if path.startswith("/") and not path.startswith("/api/"):
        return "PUBLIC_WEB_BUS"

    return "UNKNOWN"


def is_bus_powered(bus: str) -> bool:
    if bus == "UNKNOWN":
        return True
    return _get_bus_states().get(bus, "OFF") == "ON"


def get_bus_state(bus: str) -> str:
    return _get_bus_states().get(bus, "OFF")


def get_all_buses() -> dict:
    return _get_bus_states().copy()
