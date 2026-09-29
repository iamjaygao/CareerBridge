"""
Helpers for real concurrency tests: N threads, each with its own database
connection, released together by a barrier.

These tests need PostgreSQL (row locks, unique-index waits under READ
COMMITTED). SQLite serialises writers and cannot exercise the races, so the
tests are skipped there and run in the backend-postgres CI job.
"""

import os
import threading
import unittest

from django.db import connection

ITERATIONS = int(os.environ.get('CONCURRENCY_ITERATIONS', '100'))

requires_postgres = unittest.skipUnless(
    connection.vendor == 'postgresql',
    'requires PostgreSQL; runs in the backend-postgres CI job',
)


def run_concurrently(n, target, timeout=60):
    """Run target(i) for i in range(n) at the same instant; return results in order."""
    barrier = threading.Barrier(n)
    results = [None] * n
    errors = []

    def worker(i):
        try:
            barrier.wait(timeout=timeout)
            results[i] = target(i)
        except Exception as exc:  # surfaced to the test below
            errors.append((i, repr(exc)))
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout)
    alive = [t for t in threads if t.is_alive()]
    if alive:
        raise AssertionError(f'{len(alive)} threads did not finish (deadlock?)')
    if errors:
        raise AssertionError(f'worker errors: {errors}')
    return results
