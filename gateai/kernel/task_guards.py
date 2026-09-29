"""
Bus gating for periodic tasks.

Buses gate HTTP requests in the middleware, but beat runs tasks directly.
A task of an unlaunched module must therefore check its own bus and do
nothing while that bus is OFF.
"""

import functools

from celery import shared_task

from kernel.policies.bus_power import is_bus_powered

SKIPPED = 'skipped: bus off'


def bus_gated_task(bus, **task_options):
    """Like @shared_task, but the task is a no-op while `bus` is OFF."""
    def decorate(func):
        @functools.wraps(func)
        def run(*args, **kwargs):
            if not is_bus_powered(bus):
                return SKIPPED
            return func(*args, **kwargs)
        return shared_task(required_bus=bus, **task_options)(run)
    return decorate
