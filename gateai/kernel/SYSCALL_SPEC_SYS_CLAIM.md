# Kernel Syscall: `sys_claim`

## Overview

`sys_claim` is GateAI's first production-grade kernel syscall - the **ONLY** legal entry point from User Space into Kernel Space for claiming physical resources.

This is **NOT** an API helper. This is an **OS-grade system call** with kernel-level guarantees.

---

## Contract Guarantees

✅ **Deterministic**  
Same inputs → same outputs (always)

✅ **Physically Safe**  
Survives PostgreSQL concurrency with UNIQUE constraint races

✅ **ABI-Compliant**  
Uses `kernel.abi` classify_success/classify_failure

✅ **Auditable**  
`KernelAuditLog` entry ALWAYS created (even on crash)

✅ **Broken-Transaction Safe**  
Never queries inside failed atomic blocks

✅ **Re-Entrant Safe**  
Same owner can re-claim without conflict

✅ **Traceable**  
Returns `audit_id` (trace ID) to caller

✅ **Domain-Agnostic**  
Kernel-level only, no business logic imports

---

## Function Signature

```python
from kernel.syscalls import sys_claim, SyscallResult

def sys_claim(payload: Dict[str, Any]) -> SyscallResult:
    """
    Kernel syscall: Claim a physical resource.
    
    Returns:
        SyscallResult with audit_id, outcome dict, and outcome_code
    """
```

---

## Payload Schema

### Required Fields

```python
{
    "decision_id": str,       # Decision context ID
    "context_hash": str,      # Request context hash (for idempotency)
    "resource_type": str,     # Type of resource (APPOINTMENT, STAGING_SERVER, etc.)
    "resource_id": int|str,   # ID of resource to claim
    "owner_id": int|str,      # ID of claiming owner (User PK)
    
    # ONE of these is required:
    "expires_at": datetime,       # Explicit expiration time
    "duration_seconds": int,      # OR duration from now
}
```

### Optional Fields

```python
{
    "resource_key": str,  # Optional specificity key for composite locks
}
```

---

## Return Value: `SyscallResult`

```python
@dataclass
class SyscallResult:
    audit_id: str         # Trace ID (maps to KernelAuditLog.event_id)
    outcome: dict         # Full outcome dict (serialized KernelOutcome)
    outcome_code: str     # Quick status (OK/REPLAY/CONFLICT/REJECTED/FAILED_*)
```

---

## Outcome Codes

### Success Codes

**`OK`** - Resource claimed successfully  
- `retryable`: False  
- `terminal`: True  
- `http_hint`: 200

**`REPLAY`** - Idempotent replay detected (operation already completed)  
- `retryable`: False  
- `terminal`: True  
- `http_hint`: 200

### Failure Codes

**`CONFLICT`** - Resource conflict (another owner holds lock)  
- `retryable`: **True** (retry recommended)  
- `terminal`: False  
- `http_hint`: 409

**`REJECTED`** - Invalid payload or policy violation  
- `retryable`: False  
- `terminal`: True  
- `http_hint`: 400

**`FAILED_RETRYABLE`** - Transient failure  
- `retryable`: True  
- `terminal`: False  
- `http_hint`: 503

**`FAILED_FATAL`** - Permanent failure  
- `retryable`: False  
- `terminal`: True  
- `http_hint`: 500

---

## Usage Examples

### Basic Claim

```python
from kernel.syscalls import sys_claim
from datetime import timedelta
from django.utils import timezone

payload = {
    "decision_id": "appt_booking:12345",
    "context_hash": "user1_slot2_2026-01-06",
    "resource_type": "APPOINTMENT",
    "resource_id": 42,
    "owner_id": 1,
    "duration_seconds": 3600,  # 1 hour lock
}

result = sys_claim(payload)

if result.outcome_code == "OK":
    print(f"✅ Lock claimed! Audit ID: {result.audit_id}")
    print(f"Lock ID: {result.outcome['extras']['lock_id']}")
elif result.outcome_code == "CONFLICT":
    print(f"⚠️ Resource already claimed by another user")
    print(f"Retryable: {result.outcome['retryable']}")
elif result.outcome_code == "REPLAY":
    print(f"✅ Idempotent replay - operation already completed")
```

### Using Explicit Expiration

```python
expires_at = timezone.now() + timedelta(hours=2)

payload = {
    "decision_id": "staging_deploy:789",
    "context_hash": "deploy_v1.2.3",
    "resource_type": "STAGING_SERVER",
    "resource_id": "server-01",
    "owner_id": 5,
    "expires_at": expires_at,
}

result = sys_claim(payload)
```

### With Resource Key (Composite Locks)

```python
payload = {
    "decision_id": "api_integration:456",
    "context_hash": "stripe_checkout",
    "resource_type": "API_CREDENTIAL",
    "resource_id": "stripe_key_1",
    "owner_id": 10,
    "resource_key": "payment_session_abc123",
    "duration_seconds": 300,  # 5 minutes
}

result = sys_claim(payload)
```

---

## Behavior Specification

### Step 1: Audit Root Allocation

**ALWAYS** create `KernelAuditLog` entry **FIRST**, before any CAS/lock attempt.

```python
event_type = "SYS_CLAIM"
status = "EMITTED"  # Syscall in flight
payload = {"request": payload}
```

Even if syscall crashes, this audit MUST exist.

### Step 2: Idempotency CAS

Check if operation already processed:

```python
idempotency_key = f"sys_claim:{decision_id}:{context_hash}"
claimed, record = claim_idempotency_key(...)
```

If `claimed == False`:
- Return `REPLAY` outcome immediately
- No lock attempt made

### Step 3: Shadow Pre-Check

Before physical claim, check for expired locks:

```python
existing = ResourceLock.objects.filter(
    resource_type=...,
    resource_id=...,
).first()

if existing and existing.is_expired:
    existing.delete()  # Best-effort cleanup
```

**Rationale:** Distinguishes "stale lock" from "real concurrent owner"

### Step 4: Physical Claim (Atomic)

Inside `transaction.atomic()`:

```python
lock = ResourceLock.objects.create(
    decision_id=decision_id,
    resource_type=resource_type,
    resource_id=resource_id,
    owner_id=owner_id,
    expires_at=expires_at,
    status='active',
)
```

On success:
- Return `OK` outcome
- Include `lock_id` in extras

### Step 5: Conflict Handling

If `IntegrityError` from `UNIQUE(resource_type, resource_id)`:

**🚨 CRITICAL: Query OUTSIDE atomic block**

```python
try:
    with transaction.atomic():
        ResourceLock.objects.create(...)
except IntegrityError:
    # OUTSIDE atomic block - safe to query
    existing = ResourceLock.objects.filter(...).first()
    
    if existing and str(existing.owner_id) == str(owner_id):
        # RE-ENTRANT: Same owner already holds lock
        return OK (ownership guard)
    else:
        # REAL CONFLICT: Different owner holds lock
        return CONFLICT
```

**Re-Entrant Detection (Ownership Guard):**
- Same owner can re-claim across different decisions
- Treated as SUCCESS, not conflict
- Prevents false 409s for same user

**Real Conflict:**
- Different owner holds lock
- Return `CONFLICT` with retry hint

### Step 6: Audit Closure

Store outcome in audit log:

```python
# Store outcome dict
KernelAuditLog.store_outcome(audit.event_id, outcome)

# Map outcome → status
status = map_outcome_to_status(outcome)

# Update audit
KernelAuditLog.safe_mark_handled(
    event_id=audit.event_id,
    status=status,
)
```

Return `SyscallResult` to caller.

---

## Error Handling

### Invalid Payload

**Missing required fields:**
```python
result.outcome_code == "REJECTED"
result.outcome["error_code"] == "KERNEL/INVALID_PAYLOAD"
```

**Missing expires_at/duration_seconds:**
```python
result.outcome_code == "REJECTED"
result.outcome["internal_reason"] == "Payload must include..."
```

### Resource Conflicts

**Different owner holds lock:**
```python
result.outcome_code == "CONFLICT"
result.outcome["retryable"] == True
result.outcome["http_hint"] == 409
```

**Same owner re-claims (re-entrant):**
```python
result.outcome_code == "OK"
result.outcome["public_message"] == "Re-entrant claim detected..."
```

### Unexpected Errors

**Generic failure:**
```python
result.outcome_code == "FAILED_RETRYABLE"
result.outcome["retryable"] == True
```

---

## Testing

### Run Test Suite

```bash
cd gateai
python manage.py test kernel.tests.test_syscalls
```

### Test Coverage

- ✅ Basic claim success
- ✅ Idempotency replay (double-click)
- ✅ Physical conflict (different owner)
- ✅ Re-entrant claim (same owner)
- ✅ Expired lock cleanup
- ✅ Invalid payload validation
- ✅ Audit log always created
- ✅ ABI outcome structure
- ✅ Different resource types no conflict
- ✅ Deterministic behavior

---

## Integration Example

### API Endpoint (User Space)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from kernel.syscalls import sys_claim

class ClaimResourceView(APIView):
    def post(self, request):
        # Build syscall payload from API request
        payload = {
            "decision_id": f"booking:{request.data['booking_id']}",
            "context_hash": self._compute_context_hash(request),
            "resource_type": "APPOINTMENT",
            "resource_id": request.data["slot_id"],
            "owner_id": request.user.id,
            "duration_seconds": 3600,
        }
        
        # Invoke syscall
        result = sys_claim(payload)
        
        # Map outcome to HTTP response
        if result.outcome_code == "OK":
            return Response({
                "success": True,
                "audit_id": result.audit_id,
                "lock_id": result.outcome["extras"]["lock_id"],
            }, status=200)
        
        elif result.outcome_code == "REPLAY":
            return Response({
                "success": True,
                "message": "Already claimed",
                "audit_id": result.audit_id,
            }, status=200)
        
        elif result.outcome_code == "CONFLICT":
            return Response({
                "success": False,
                "error": "Resource unavailable",
                "retryable": True,
                "audit_id": result.audit_id,
            }, status=409)
        
        else:
            return Response({
                "success": False,
                "error": result.outcome["public_message"],
                "audit_id": result.audit_id,
            }, status=result.outcome.get("http_hint", 500))
    
    def _compute_context_hash(self, request):
        import hashlib
        context = f"{request.user.id}:{request.data['slot_id']}"
        return hashlib.sha256(context.encode()).hexdigest()[:16]
```

---

## Auditability

Every `sys_claim` invocation creates a `KernelAuditLog` entry:

```python
audit = KernelAuditLog.objects.get(event_id=result.audit_id)

print(f"Event Type: {audit.event_type}")
print(f"Decision ID: {audit.decision_id}")
print(f"Status: {audit.status}")
print(f"Request: {audit.payload['request']}")
print(f"Outcome: {audit.payload['abi']}")
```

**Audit fields:**
- `event_id` (UUID) - Trace ID
- `event_type` - "SYS_CLAIM"
- `decision_id` - Decision context
- `status` - HANDLED/REJECTED/FAILED
- `payload.request` - Original syscall payload
- `payload.abi` - KernelOutcome dict
- `created_at` - Syscall invocation time
- `handled_at` - Syscall completion time
- `latency_ms` - Execution duration

---

## Architecture Notes

### Why Physical Delete?

Syscall uses **physical delete** for expired locks (not soft delete):
- Allows immediate re-locking of same resource tuple
- Prevents soft-delete confusion
- Audit trail is in `KernelAuditLog`, not `ResourceLock.status`

### Why Re-Entrant Detection?

Same owner claiming same resource across different decisions should **succeed**, not conflict:
- User refreshes page → same claim
- Retry logic → same claim
- Prevents false 409s for legitimate retries

This is the **Ownership Guard** pattern.

### Why Shadow Pre-Check?

Checking for expired locks before physical claim:
- Reduces false conflicts
- Distinguishes "stale lock" from "active contention"
- Best-effort cleanup (non-blocking)

### Why Broken-Transaction Safety?

PostgreSQL quirk: After `IntegrityError` inside `transaction.atomic()`, **all subsequent queries fail** until block exits.

**Incorrect (will crash):**
```python
with transaction.atomic():
    try:
        ResourceLock.objects.create(...)
    except IntegrityError:
        # ❌ CRASH: query inside broken transaction
        existing = ResourceLock.objects.filter(...).first()
```

**Correct:**
```python
try:
    with transaction.atomic():
        ResourceLock.objects.create(...)
except IntegrityError:
    # ✅ SAFE: query outside atomic block
    existing = ResourceLock.objects.filter(...).first()
```

---

## Performance Characteristics

**Hot Path Optimization:**
- Idempotency check uses hot-path `KernelIdempotencyRecord` table
- No full `KernelAuditLog` scan for replay detection
- B-Tree locality optimized for PostgreSQL

**Latency Profile:**
- Success case: ~5-10ms (1 audit write, 1 lock create)
- Idempotent replay: ~2-5ms (1 audit write, 1 idempotency check)
- Conflict case: ~10-15ms (1 audit write, 1 failed create, 1 conflict query)

**Scalability:**
- Supports high concurrency via PostgreSQL row locks
- UNIQUE constraint provides physical arbitration
- No application-level locking required

---

## Future Extensions

Potential syscall additions:

- `sys_release(audit_id)` - Release lock by audit ID
- `sys_extend(audit_id, duration)` - Extend lock expiration
- `sys_transfer(audit_id, new_owner_id)` - Transfer lock ownership
- `sys_query(resource_type, resource_id)` - Query lock status

---

## Contact

For questions or issues:
- Review: `docs/GATEAI_OS_CONTRACT.md`
- Check: `kernel/abi.py` for outcome codes
- File issue with `[KERNEL]` prefix

---

**GateAI Kernel Syscalls v1.0**  
**OS-Grade | Deterministic | Auditable**

