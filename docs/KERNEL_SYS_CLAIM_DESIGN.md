"""
# GateAI Kernel — sys_claim Arbitration & Idempotency

## Overview

This module implements a **kernel-grade syscall** (`sys_claim`) that provides
deterministic, auditable, and fail-closed resource claiming semantics.

The design goal is to ensure:
- **Exactly one winner** per resource arbitration window
- **Idempotent replay** for identical requests
- **Terminal conflict** for deterministic losers
- **Zero retry amplification** (no accidental 503 storms)

This is enforced at the **kernel layer**, not at the application layer.

---

## Core Guarantees

### 1. Deterministic Arbitration
- Arbitration is based on `(resource_id, bucket_start, context_hash, owner_id)`
- Exactly one request can win per bucket
- All others deterministically lose (HTTP 409)

### 2. Idempotency as First-Class Kernel Primitive
- Idempotency key is derived from:
  `sys_claim:{resource_type}:{resource_id}:{context_hash}`
- Repeated identical requests return **REPLAY** (HTTP 200)
- No re-execution after success

### 3. Fail-Closed Semantics
- Any exception inside arbitration:
  - NEVER leaks as HTTP 503
  - Is treated as a **deterministic loser**
  - Returns HTTP 409 (terminal, non-retryable)

### 4. Immutable Audit Trail
- Winner selection is persisted atomically
- `owner_id` and `context_hash` are captured on initial insert
- Arbitration records are append-only and auditable

---

## HTTP Outcome Semantics

| Scenario                               | HTTP | Outcome        | Retry |
|----------------------------------------|------|----------------|-------|
| First winner                           | 200  | SUCCESS        | No    |
| Same request replay                   | 200  | REPLAY         | No    |
| Deterministic arbitration loser        | 409  | CONFLICT       | No    |
| Invalid input / malformed syscall     | 400  | REJECTED       | No    |
| Kernel invariant violation             | 500  | FAILED_FATAL   | No    |

**HTTP 503 is reserved ONLY for true infrastructure failures.**

---

## Adversarial Validation

The kernel was validated using a hostile simulation harness:

- Multi-context same resource flood
- Same context, different owners
- Backoff violation retry loops
- decision_id collision attacks

### Result:
✅ **ZERO HTTP 503**
✅ Kernel remains stable under retry floods
✅ Deterministic outcomes preserved

---

## Why This Matters

This design:
- Prevents retry storms
- Makes kernel behavior explainable
- Enables post-mortem auditability
- Scales safely under adversarial conditions

This is **OS-grade behavior**, not application-level best effort.
"""
