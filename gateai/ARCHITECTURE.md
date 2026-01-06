# GateAI Kernel Architecture

## Design Goals
The GateAI Kernel is designed to provide a robust, deterministic execution environment for high-stakes resource orchestration. Its architectural decisions prioritize:
- **Determinism**: Identical inputs to the syscall layer must result in identical state transitions and audit records.
- **Physical Safety**: Zero-tolerance for resource over-provisioning or "double-booking" through database-enforced integrity.
- **Failure Containment**: Isolation of application-level failures from kernel-level state, ensuring no partial or corrupted transitions.
- **Auditability**: Complete, immutable history of all kernel decisions (audits) as the primary source of truth.

## High-Level Architecture
The system is built on a layered architecture that strictly separates kernel operations from user-space business logic.
- **Kernel Syscall Layer**: The single entry point for all operations. Enforces ABI compliance and failure classification.
- **Idempotency Store**: A Compare-And-Swap (CAS) mechanism ensuring that any operation with the same decision context is processed exactly once.
- **ResourceLock Model**: The physical representation of held resources, secured by PostgreSQL UNIQUE constraints.
- **Audit Log**: A comprehensive record of every syscall attempt, status, and outcome.
- **Observability APIs**: Read-only endpoints for status and telemetry streaming.
- **Pulse UI**: A non-mutating visualization layer for real-time monitoring of the kernel's state.

## Syscall Lifecycle (sys_claim)
The standard execution flow of the `sys_claim` syscall follows a rigid pipeline:
1.  **Payload Validation**: Syntactic and semantic check of inputs (decision IDs, resource identities, durations).
2.  **Audit Root Creation**: Allocation of a high-level audit record before any state manipulation occurs. This ensures even catastrophic crashes are recorded.
3.  **Idempotency CAS**: Checking the `KernelIdempotencyRecord` to detect and replay successful historical operations.
4.  **Physical Claim**: An atomic attempt to create a `ResourceLock`. This step leverages database constraints to resolve low-level race conditions.
5.  **Conflict vs Re-entry Resolution**: If a claim fails, the kernel performs a read-only check (outside broken transaction blocks) to distinguish between a legitimate resource conflict and a re-entrant request from the same owner.
6.  **Outcome Classification**: Mapping the internal result to a stable ABI execution code (OK, CONFLICT, etc.).

## Transaction Safety Model
The kernel implements a specialized safety model to handle PostgreSQL's "broken transaction" behavior:
- **Post-Integrity Handling**: After a UNIQUE constraint violation (`IntegrityError`), the current database transaction is poisoned. No further queries are permitted.
- **Atomic Deferral**: The kernel uses a flag-based deferral mechanism to exit the poisoned `transaction.atomic()` block before attempting any diagnostic queries (like re-entry checks).
- **Outer Atomic Guard**: If the kernel detects it is being called within an outer `transaction.atomic()` (from a caller), it refuses post-conflict diagnosis and returns `FAILED_RETRYABLE` to ensure systematic rollback and prevent data corruption.

## Failure Semantics
Execution results are categorized using the standardized Kernel ABI:
- **REJECTED**: The request was malformed or violated a contract (e.g., negative duration). No retry recommended.
- **CONFLICT**: A physical resource is currently held by another owner. Retry recommended after lock expiration.
- **FAILED_RETRYABLE**: A transient system failure occurred (e.g., atomic context violation). Safe to retry.
- **FAILED_FATAL**: An unexpected, permanent system error. Do not retry without manual intervention.

Explicit classification ensures that calling systems can implement deterministic error-handling logic without guessing the cause of failure.

## Observability & Truth Model
Monitoring is strictly segregated from control:
- **Read-Only**: Observability endpoints and the Pulse UI have no ability to mutate kernel state.
- **Audit as Truth**: The system of record is the `KernelAuditLog`. State visualization in the UI is a projection of this log.
- **Traceability**: Every operation is tied to a `TraceID`, connecting the external request to internal decision logs and database locks.

## Non-Goals
To maintain architectural purity, the kernel explicitly avoids:
- **Auto-Renewal**: System leases must be explicitly reclaimed by owners.
- **Implicit Retries**: The kernel reports status; the caller (user-space) owns retry policy.
- **Side Effects on Failure**: If a syscall fails, no secondary actions (like release of other locks) are performed within the kernel scope.

## Summary
The GateAI Kernel architecture provides a predictable and physically safe foundation for autonomous resource allocation. By combining strict entrypoint controls, deterministic outcome classification, and defensive transaction management, it ensures system integrity even under extreme concurrency or execution failure.
