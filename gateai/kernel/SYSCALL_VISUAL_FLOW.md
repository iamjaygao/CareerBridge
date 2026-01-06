# 🔄 sys_claim Visual Flow Reference

## Complete Execution Flow

```
USER SPACE (API/View)
    │
    │ payload = {
    │   "decision_id": "...",
    │   "context_hash": "...",
    │   "resource_type": "...",
    │   "resource_id": ...,
    │   "owner_id": ...,
    │   "duration_seconds": ...
    │ }
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│                  KERNEL SPACE BOUNDARY                        │
│                  sys_claim(payload)                           │
└───────────────────────────────────────────────────────────────┘
    │
    │ Step 0: Validate Payload
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│ ❓ Payload Valid?                                             │
└─────────┬─────────────────────────────────────────────────────┘
    NO    │    YES
    │     │
    ▼     │
┌─────────────────┐
│ ❌ REJECTED     │
│ Missing fields  │
│ audit created   │
│ return early    │
└─────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────┐
│ Step 1: Allocate Audit Root (ALWAYS)                         │
│                                                               │
│ audit = KernelAuditLog.create(                               │
│     event_id=UUID(),                                         │
│     event_type="SYS_CLAIM",                                  │
│     status="EMITTED",                                        │
│     payload={"request": payload}                             │
│ )                                                            │
│                                                               │
│ audit_id = audit.event_id  ← TRACE ID                       │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────────┐
│ Step 2: Idempotency CAS                                       │
│                                                               │
│ claimed, record = claim_idempotency_key(                     │
│     idempotency_key=f"sys_claim:{decision_id}:{hash}",      │
│     event_type="SYS_CLAIM",                                  │
│     decision_id=...,                                         │
│     context_hash=...,                                        │
│ )                                                            │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                    ┌─────┴──────┐
                    │  Claimed?  │
                    └─────┬──────┘
              NO (replay) │    YES (first call)
         ┌────────────────┴───────────────┐
         ▼                                ▼
┌──────────────────────┐       ┌──────────────────────┐
│ ✅ REPLAY            │       │ Step 3: Shadow       │
│                      │       │ Pre-Check            │
│ outcome = classify_  │       │                      │
│   success(           │       │ existing = ...first()│
│     claimed=False    │       │                      │
│   )                  │       │ if expired:          │
│                      │       │   delete()           │
│ update_audit()       │       └──────────┬───────────┘
│ return REPLAY        │                  │
└──────────────────────┘                  ▼
                          ┌───────────────────────────────┐
                          │ Step 4: Physical Claim        │
                          │                               │
                          │ try:                          │
                          │   with transaction.atomic():  │
                          │     ResourceLock.objects.     │
                          │       create(                 │
                          │         decision_id=...,      │
                          │         resource_type=...,    │
                          │         resource_id=...,      │
                          │         owner_id=...,         │
                          │         expires_at=...,       │
                          │       )                       │
                          └────────────┬──────────────────┘
                                       │
                              ┌────────┴─────────┐
                              │   Success?       │
                              └────────┬─────────┘
                          YES          │     NO (IntegrityError)
                 ┌───────────────────┴─────────────────────┐
                 ▼                                         ▼
┌────────────────────────────────┐       ┌─────────────────────────────────┐
│ ✅ OK                          │       │ Step 5: Conflict Handling       │
│                                │       │                                 │
│ outcome = classify_success(    │       │ except IntegrityError:          │
│   claimed=True,                │       │   # ⚠️ OUTSIDE atomic block     │
│   message="Lock claimed",      │       │   existing = ResourceLock...    │
│   lock_id=lock.id              │       │                                 │
│ )                              │       │   ❓ Same owner?                │
│                                │       └──────────┬──────────────────────┘
│ update_audit(outcome)          │              YES │  NO
│ return OK                      │     ┌────────────┴────────────┐
└────────────────────────────────┘     ▼                         ▼
                          ┌──────────────────────┐  ┌─────────────────────┐
                          │ ✅ RE-ENTRANT        │  │ ⚠️ CONFLICT         │
                          │                      │  │                     │
                          │ Same owner holds     │  │ Different owner     │
                          │ lock (ownership      │  │ holds lock          │
                          │ guard)               │  │                     │
                          │                      │  │ outcome = classify_ │
                          │ outcome = classify_  │  │   failure(          │
                          │   success(           │  │     resource_       │
                          │     claimed=True,    │  │     conflict=True   │
                          │     message="Re-     │  │   )                 │
                          │       entrant"       │  │                     │
                          │   )                  │  │ retryable=True      │
                          │                      │  │ http_hint=409       │
                          │ return OK            │  │ return CONFLICT     │
                          └──────────────────────┘  └─────────────────────┘
                                       │                      │
                                       └──────────┬───────────┘
                                                  │
                                                  ▼
                          ┌───────────────────────────────────────────┐
                          │ Step 6: Audit Closure (Best-Effort)      │
                          │                                           │
                          │ store_outcome(audit_id, outcome)          │
                          │ status = map_outcome_to_status(outcome)   │
                          │ safe_mark_handled(audit_id, status)       │
                          └─────────────────────┬─────────────────────┘
                                                │
                                                ▼
                          ┌───────────────────────────────────────────┐
                          │ Return SyscallResult                      │
                          │                                           │
                          │ return SyscallResult(                     │
                          │     audit_id=str(audit.event_id),        │
                          │     outcome=outcome.to_dict(),           │
                          │     outcome_code=outcome.outcome_code,   │
                          │ )                                        │
                          └─────────────────────┬─────────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────┐
│                  KERNEL SPACE BOUNDARY                        │
│                  return to caller                             │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
USER SPACE (API/View)
    │
    │ result = sys_claim(payload)
    │
    │ if result.outcome_code == "OK":
    │     return 200 OK
    │ elif result.outcome_code == "CONFLICT":
    │     return 409 Conflict
    │ elif result.outcome_code == "REPLAY":
    │     return 200 OK (idempotent)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Outcome Decision Tree

```
sys_claim(payload)
    │
    ├─ Payload invalid?
    │   └─► REJECTED (400)
    │
    ├─ Idempotency replay?
    │   └─► REPLAY (200)
    │
    ├─ Physical claim succeeds?
    │   └─► OK (200)
    │
    ├─ IntegrityError (UNIQUE conflict)?
    │   │
    │   ├─ Same owner holds lock?
    │   │   └─► OK (200) [Re-entrant]
    │   │
    │   └─ Different owner holds lock?
    │       └─► CONFLICT (409) [Retryable]
    │
    └─ Unexpected error?
        └─► FAILED_RETRYABLE (503)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## State Transition Diagram

```
                 ┌─────────────┐
                 │   INITIAL   │
                 │   (User     │
                 │   Space)    │
                 └──────┬──────┘
                        │
            ┌───────────▼───────────┐
            │  AUDIT ROOT ALLOCATED │
            │  (KernelAuditLog)     │
            │  status=EMITTED       │
            └───────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────┐  ┌────────────────┐  ┌──────────┐
│  REPLAY   │  │  CLAIMED (OK)  │  │ CONFLICT │
│ Terminal  │  │    Terminal    │  │Retryable │
└───────────┘  └────────────────┘  └──────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   AUDIT UPDATED       │
            │   status=HANDLED/     │
            │          REJECTED/    │
            │          FAILED       │
            └───────────┬───────────┘
                        │
                        ▼
                ┌───────────────┐
                │   RETURN TO   │
                │   USER SPACE  │
                └───────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Broken-Transaction Safety Pattern

### ❌ INCORRECT (Will Crash)

```python
with transaction.atomic():
    try:
        ResourceLock.objects.create(...)  # IntegrityError
    except IntegrityError:
        # ❌ Transaction is BROKEN here
        existing = ResourceLock.objects.filter(...).first()
        # ❌ CRASH: "current transaction is aborted"
```

### ✅ CORRECT (Safe)

```python
try:
    with transaction.atomic():
        ResourceLock.objects.create(...)  # IntegrityError
except IntegrityError:
    # ✅ Outside atomic block - transaction closed
    existing = ResourceLock.objects.filter(...).first()
    # ✅ SAFE: new transaction context
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Re-Entrant Detection (Ownership Guard)

```
Scenario: User refreshes page during booking

Call 1:
┌────────────────────────────────────────┐
│ decision_id: "booking:A"               │
│ owner_id: 1                            │
│ resource_id: 42                        │
└──────────────┬─────────────────────────┘
               │
               ▼
        [ResourceLock created]
               │
               ▼
        outcome_code = OK ✅

Call 2 (refresh):
┌────────────────────────────────────────┐
│ decision_id: "booking:B"  ← Different! │
│ owner_id: 1               ← Same!      │
│ resource_id: 42           ← Same!      │
└──────────────┬─────────────────────────┘
               │
               ▼
        [IntegrityError: UNIQUE conflict]
               │
               ▼
        Query existing lock (outside atomic)
               │
               ▼
        ❓ owner_id match?
               │
         ┌─────┴─────┐
        YES           NO
         │             │
         ▼             ▼
    OK (re-entrant)  CONFLICT
    ✅ Same user     ⚠️ Different user
```

**Without ownership guard:** User gets 409 CONFLICT ❌  
**With ownership guard:** User gets 200 OK ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Shadow Pre-Check (Expired Lock Cleanup)

```
Timeline:

T=0  Lock created by User A
     expires_at = T+1hour
     ┌──────────────────┐
     │ ResourceLock     │
     │ owner_id: A      │
     │ expires_at: T+1h │
     └──────────────────┘

T=2h Lock has expired (not cleaned yet)
     ┌──────────────────┐
     │ ResourceLock     │
     │ owner_id: A      │
     │ expires_at: T+1h │ ← EXPIRED
     └──────────────────┘

T=2h User B tries to claim
     │
     ▼
     Shadow Pre-Check:
     ┌──────────────────────────┐
     │ existing = ...first()    │
     │ if existing.is_expired:  │
     │     existing.delete() ✅ │
     └──────────────────────────┘
     │
     ▼
     Physical Claim:
     ┌──────────────────┐
     │ ResourceLock     │
     │ owner_id: B      │
     │ expires_at: T+3h │ ← NEW
     └──────────────────┘
     │
     ▼
     outcome_code = OK ✅

Without shadow pre-check:
  User B gets CONFLICT (false alarm) ❌

With shadow pre-check:
  User B gets OK (expired lock cleaned) ✅
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Idempotency CAS Flow

```
Double-Click Scenario:

Click 1:
┌────────────────────────────────────────┐
│ decision_id: "booking:123"             │
│ context_hash: "user1_slot42"           │
└──────────────┬─────────────────────────┘
               │
               ▼
    claim_idempotency_key(...)
               │
         ┌─────┴─────┐
         │ B-Tree    │
         │ INSERT    │
         └─────┬─────┘
               │
           claimed=True ✅
               │
               ▼
        [Proceed to physical claim]
               │
               ▼
        outcome_code = OK

Click 2 (within 100ms):
┌────────────────────────────────────────┐
│ decision_id: "booking:123"  ← Same     │
│ context_hash: "user1_slot42"  ← Same   │
└──────────────┬─────────────────────────┘
               │
               ▼
    claim_idempotency_key(...)
               │
         ┌─────┴─────┐
         │ B-Tree    │
         │ CONFLICT  │ ← Key exists
         └─────┬─────┘
               │
           claimed=False ❌
               │
               ▼
        [Skip physical claim]
               │
               ▼
        outcome_code = REPLAY
        message = "Operation already completed"
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Audit Trail Timeline

```
T=0ms    sys_claim(payload) called
         │
         ▼
T=1ms    KernelAuditLog created
         ┌─────────────────────────────┐
         │ event_id: UUID (audit_id)   │
         │ event_type: SYS_CLAIM       │
         │ status: EMITTED             │
         │ created_at: T=1ms           │
         │ payload: {"request": ...}   │
         └─────────────────────────────┘
         │
         ▼
T=2ms    Idempotency check (CAS)
         │
         ▼
T=3ms    Physical claim attempt
         │
         ▼
T=8ms    Outcome determined
         │
         ▼
T=9ms    Audit updated
         ┌─────────────────────────────┐
         │ status: HANDLED             │
         │ handled_at: T=9ms           │
         │ latency_ms: 8               │
         │ payload: {                  │
         │   "request": ...,           │
         │   "abi": {                  │
         │     "outcome_code": "OK",   │
         │     "retryable": false,     │
         │     ...                     │
         │   }                         │
         │ }                           │
         └─────────────────────────────┘
         │
         ▼
T=10ms   Return to caller
         │
         ▼
         SyscallResult(
             audit_id="...",
             outcome={...},
             outcome_code="OK"
         )
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**GateAI Kernel Syscalls v1.0**  
**Visual Reference Guide**

