# GateAI Kernel / CareerBridge Boundary Map

This document defines **hard architectural boundaries** between the
GateAI Kernel (OS / Infrastructure) and the CareerBridge Application (Client).

These boundaries are **governance rules**, not implementation suggestions.

---

## 1. Layer Definitions

### A. GateAI Kernel (Read-Only Infrastructure)

**Role**
- Deterministic execution
- Resource arbitration
- Audit & trace anchoring
- Syscall ABI enforcement

**Rules**
- MUST be treated as immutable
- MUST NOT import application/business modules
- MUST NOT contain domain logic

**Owned Paths**
- `gateai/kernel/`
- `gateai/kernel/syscalls.py`
- `gateai/kernel/models.py`
- `gateai/decision_slots/models.py` (ResourceLock ONLY)

---

### B. Kernel Interface Layer (Bus / Boundary)

**Role**
- Explicit communication boundary between App and Kernel
- SDKs, event envelopes, transport

**Rules**
- May reference kernel types
- Must NOT implement business logic
- Must NOT mutate application state directly

**Owned Paths**
- `gateai/kernel/agent_sdk.py`
- `gateai/gateai/kernel_events.py`
- `gateai/signal_delivery/`

---

### C. Application Layer (CareerBridge)

**Role**
- Business workflows
- Payments, appointments, mentors, ATS logic
- UI and user interaction

**Rules**
- MUST NOT import kernel internals
- MUST interact with kernel via syscalls or kernel events only
- MUST NOT directly mutate kernel-governed state

**Owned Paths**
- `gateai/appointments/`
- `gateai/payments/`
- `gateai/human_loop/` (excluding kernel primitives)
- `gateai/ats_signals/`
- `gateai/chat/`
- `gateai/dashboard/`
- `gateai/adminpanel/`
- `frontend/`
- `JobCrawler/`
- `ResumeMatcher/`

---

### D. Shared Utilities (Minimal & Non-Kernel)

**Role**
- Generic helpers only

**Rules**
- Must be domain-agnostic
- Must not depend on kernel or application logic

**Owned Paths**
- `gateai/external_services/`

---

## 2. Forbidden Dependencies (Hard Rules)

- **Kernel MUST NOT import**:
  - `appointments.*`
  - `payments.*`
  - `mentors.*`
  - `ats_signals.*`

- **Application MUST NOT**:
  - Import `ResourceLock` directly
  - Write `TimeSlot.reserved_until`
  - Write `Appointment.status` as a state machine transition
  - Bypass `sys_claim` or kernel events
  - Import any module under gateai/kernel/*
  (except via approved interface/client abstractions)

---

## 3. Known Boundary Violations (Tracked)

These violations are **frozen** and must not expand:

1. **Manual slot locking**: in `decision_slots/views.py`
2. **Direct appointment status mutation**: in `payments/views.py`
3. **Mixed kernel + application code**: under `decision_slots/`

Fixes are planned in Phase-1 refactors.
Phase-1 refactors will replace all direct state mutations
with kernel-mediated syscalls or kernel-signed events.

---

## 4. Enforcement Principle

> Kernel is the roadbed.  
> Applications are vehicles.  
> No asphalt is poured inside the car.

All future changes must comply with this boundary map.
