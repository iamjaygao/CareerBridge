# GateAI Kernel Architecture

## The Kernel Laws
High-stakes resource orchestration requires a set of immutable guarantees. The GateAI Kernel operates under three core laws:
1. **The Law of Idempotency**: An identical resource request must always yield an identical system outcome. The kernel enforces this via a mandatory Compare-And-Swap (CAS) on every syscall entry.
2. **The Law of Physical Safety**: Under no circumstances shall two unique entities hold a lock on the same physical resource simultaneously. The kernel delegates this enforcement to database-level unique constraints.
3. **The Law of Atomic Safety**: A syscall must never attempt to diagnose a conflict while within a poisoned or non-deterministic transaction state. The kernel will favor a safe exit over an uncertain diagnosis.

## Design Goals
The GateAI Kernel is designed to provide a robust, deterministic execution environment for high-stakes resource orchestration. Its architectural decisions prioritize:
- **Determinism**: Identical inputs to the syscall layer must result in identical state transitions and audit records.
- **Physical Safety**: Zero-tolerance for resource over-provisioning or "double-booking" through database-enforced integrity.
- **Failure Containment**: Isolation of application-level failures from kernel-level state, ensuring no partial or corrupted transitions.
- **Auditability**: Complete, immutable history of all kernel decisions (audits) as the primary source of truth.

## High-Level Architecture
The system is built on a layered architecture that strictly separates kernel operations from user-space business logic.
- **Kernel Syscall Layer**: The single entry point for all operations. Enforces ABI compliance and failure classification.
- **Idempotency Store**: A mechanism ensuring that any operation with the same decision context is processed exactly once.
- **ResourceLock Model**: The physical representation of held resources, secured by PostgreSQL UNIQUE constraints.
- **Audit Log**: A comprehensive record of every syscall attempt, status, and outcome.
- **Observability APIs**: Read-only endpoints for status and telemetry streaming.
- **Pulse UI**: A non-mutating visualization layer for real-time monitoring of the kernel's state.

## Syscall Lifecycle (sys_claim)
The standard execution flow of the `sys_claim` syscall follows a rigid pipeline:
1. **Payload Validation**: Syntactic and semantic check of inputs.
2. **Audit Root Creation**: Allocation of a high-level audit record before any state manipulation occurs.
3. **Idempotency CAS**: Checking historical records to detect and replay successful operations.
4. **Physical Claim**: An atomic attempt to create a `ResourceLock`.
5. **Conflict vs Re-entry Resolution**: If a claim fails, the kernel performs a read-only check (outside poisoned blocks) to distinguish between a resource conflict and a re-entrant request.
6. **Outcome Classification**: Mapping the internal result to a stable ABI execution code.

## Transaction Safety Model
The kernel implements a specialized safety model to handle PostgreSQL's "broken transaction" behavior:
- **Postgres Transaction Poisoning**: In PostgreSQL, once an `IntegrityError` (such as a unique constraint violation) occurs, the current transaction is marked as "broken." Any subsequent database query within that same transaction block—including read-only queries for conflict diagnosis—will terminate with a `TransactionAborted` error.
- **Atomic Deferral**: The kernel uses a flag-based deferral mechanism to exit the poisoned `transaction.atomic()` block before attempting any diagnostic queries. This ensures that re-entry detection can be performed against a fresh, viable connection state.
- **Outer Atomic Guard**: If the kernel is invoked within an outer `transaction.atomic()` block (managed by user-space), it cannot safely exit the transaction to perform diagnosis. In this state, the kernel will refuse to guess and instead returns `FAILED_RETRYABLE`, forcing the caller to roll back and retry in a clean context.

## Failure Semantics & Retry Responsibility
Execution results are categorized using the standardized Kernel ABI:
- **REJECTED**: Internal contract violation. No retry recommended.
- **CONFLICT**: Resource held by another owner. Retry recommended after lock expiration.
- **FAILED_RETRYABLE**: Transient failure (e.g., atomic context violation). Safe to retry.
- **FAILED_FATAL**: Permanent system error. Manual intervention required.

**Retry Responsibility**: The kernel is a reporting layer, not an orchestration layer. It provides precise, deterministic classification of outcomes but does not implement internal retry loops or backoff logic. User-space orchestration logic (agents, task runners) owns the responsibility for interpreting these outcomes and executing retry strategies.

## Observability & Truth Model
Monitoring is strictly segregated from control:
- **Read-Only**: Observability endpoints and the Pulse UI have no ability to mutate kernel state.
- **Audit as Truth**: The system of record is the `KernelAuditLog`. State visualization in the UI is a projection of this log.
- **Traceability**: Every operation is tied to a `TraceID`, connecting the external request to internal decision logs and database locks.

## Non-Goals
- **Auto-Renewal**: System leases must be explicitly reclaimed by owners.
- **Implicit Retries**: The kernel reports status; the caller (user-space) owns retry policy.
- **Side Effects on Failure**: Failed syscalls remain isolated; no secondary actions are performed.

## Summary
The GateAI Kernel provides a foundational safety layer for non-deterministic orchestration systems, such as LLM agents and autonomous task runners. In environments where high-latency AI decisions must interact with low-latency physical resources, the kernel acts as a hardened enforcement point. By codifying idempotency and physical safety into a deterministic ABI, the GateAI Kernel ensures that even if an agent's reasoning is probabilistic, its interaction with the physical world remains safe, auditable, and recoverable.
