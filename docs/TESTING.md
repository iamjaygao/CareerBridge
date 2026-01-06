# GateAI Kernel — Testing & Validation Strategy

This document describes how the GateAI Kernel is systematically tested to
verify its safety guarantees, determinism, and agent compliance enforcement.

The testing strategy intentionally focuses on **failure modes**, not only
happy paths.

---

## 1. Kernel Law Validation (Core Invariants)

The kernel is governed by three immutable laws:
- Idempotency
- Physical Safety
- Atomic Safety

### Covered By
- `kernel/tests/test_syscalls.py`
- Chaos Demo scripts (`scripts/sys_claim_demo.sh`, `scripts/trigger_chaos.sh`)

### Verified Properties
- Identical payloads always yield identical outcomes (OK / REPLAY).
- Under concurrent access, at most **one physical lock** can be created.
- Any syscall invoked inside an outer `transaction.atomic()` returns
  `FAILED_RETRYABLE` instead of attempting unsafe diagnosis.
- Audit persistence failures never block syscall outcomes.

**Result**: All 71 kernel tests pass with no flaky behavior.

---

## 2. Agent Compliance Enforcement Tests (Day-4C)

Agent-side behavior is enforced via a mandatory SDK layer.

### Covered By
- `agent_sdk.py`
- `kernel/tests/test_compliance_attribution.py`

### Verified Properties
- Illegal agent actions (e.g. retrying `CONFLICT` without wait) raise
  `KernelLawViolationError`.
- Unknown future `FAILED_*` outcomes are safely handled via
  `ABORT_ALERT` (forward ABI compatibility).
- Outcome-to-action mappings are centralized and immutable.

---

## 3. Context Hash Stability

Each agent decision is identified via a deterministic `context_hash`.

### Verified Properties
- Hash generation uses sorted JSON keys and compact encoding.
- Identical logical contexts produce identical hashes.
- Any semantic change (plan_step, retry_epoch, intent) produces a new hash.

This ensures stable attribution across retries and observability queries.

---

## 4. Observability & Compliance Monitoring

Kernel observability is strictly read-only.

### Covered By
- `views_observability.py`
- Pulse UI (`pulse.html`)
- `test_compliance_monitor_rapid_retry_detection`

### Verified Properties
- Rapid retry violations (<1500ms) are detected without mutating kernel state.
- Violations are attributed using `(owner_id, context_hash)`.
- Observability queries are time-bounded to avoid database pressure.

---

## 5. Chaos & Adversarial Validation

The system is intentionally stressed under invalid and adversarial conditions:

- High concurrency lock contention
- Audit database failure
- Agent retry floods
- Transaction poisoning scenarios

In all cases, the kernel favors **safe failure over unsafe progress**.

---

## Summary

The GateAI Kernel is not validated by correctness alone,
but by its ability to remain **deterministic, auditable, and safe**
under failure and adversarial behavior.

This testing strategy ensures the kernel can safely serve
non-deterministic agents (e.g. LLM-driven systems) in production environments.
