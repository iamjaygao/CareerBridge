"""
Kernel Pulse - Phase-A.1

Read-only observability plane for GateAI Kernel OS.
Provides real-time kernel state reconstruction from audit logs.

Invariants:
- READ-ONLY
- NO writes/mutations
- NO background polling
- NO calls to frozen worlds
- DB-native truth only
"""
