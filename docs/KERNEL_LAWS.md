# GateAI Kernel Laws (Developer Contract)

This document serves as the "Kernel Constitution." It must be included verbatim in LLM system prompts for any agent interacting with the GateAI Kernel.

## 1. The Three Kernel Laws
1. **The Law of Idempotency**: An identical resource request must always yield an identical system outcome. The kernel enforces this via a mandatory CAS check.
2. **The Law of Physical Safety**: Under no circumstances shall two unique entities hold a lock on the same physical resource simultaneously.
3. **The Law of Atomic Safety**: A syscall must never be processed inside a broken or non-deterministic transaction state.

## 2. Division of Responsibility
- **The Kernel**: Owns physical safety, deterministic outcome classification, and immutable audit logging. It is read-only and side-effect free on failure.
- **The Agent (User Space)**: Owns retry logic, backoff strategies, and business-level error handling based on Kernel outcomes.
- **The Observability Layer**: Provides a read-only "Pulse" of truth. It must never fabricate state or mutate kernel data.

## 3. Outcome Semantics
Agents must handle Kernel outcomes according to the following strict policy:

| Outcome | Allowed Agent Actions | Meaning |
| :--- | :--- | :--- |
| **OK** | PROCEED | Success. Resource claimed. |
| **REPLAY** | NOOP_SUCCESS, PROCEED | Idempotent success. Already processed. |
| **CONFLICT** | WAIT_RETRY | Resource busy. Wait for expiration. |
| **FAILED_RETRYABLE** | BACKOFF_RETRY | Transient failure. Exponential backoff required. |
| **REJECTED** | ABORT_ALERT | Contract violation. Invalid payload. |
| **FAILED_FATAL** | ABORT_ALERT | System failure. Human intervention needed. |

## 4. Mandatory "Do Not" List
- **Agents must NOT** attempt to write to `ResourceLock` or `KernelAuditLog` tables directly.
- **Agents must NOT** treat a `CONFLICT` outcome as a success.
- **Agents must NOT** retry a `CONFLICT` or `FAILED_RETRYABLE` immediately without an era-appropriate wait or backoff.
- **The Kernel must NOT** call LLMs or external probabilistic services.

## 5. Attribution & Fault
- **Terminal Fault**: Any violation of Kernel Laws by an Agent is considered a terminal architectural fault.
- **Immediate Termination**: Upon detecting a law violation (e.g., via `enforce_kernel_laws`), the Agent orchestrator must abort execution immediately. Silent retries of illegal actions are strictly forbidden.
- **Attribution Truth**: The `context_hash` provided by the Agent is the immutable link between Kernel outcomes and Agent decisions. Discrepancies between reasoning and context hashes are treated as system integrity failures.

## 6. How to Use This Document
This document is a formal contract. Every AI agent, system prompt, and technical reviewer must treat these laws as non-negotiable constraints on the system's architecture.
