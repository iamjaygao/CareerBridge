"""Peer mock periodic tasks. Each is a no-op while PEER_MOCK_BUS is OFF."""

from kernel.task_guards import bus_gated_task

from . import rounds


@bus_gated_task('PEER_MOCK_BUS')
def ensure_rounds():
    """Make sure the next rounds exist (idempotent; safe to run every hour)."""
    return [week_key.isoformat() for week_key in rounds.ensure_rounds()]
