# sys_claim Arbitration Order Fix (Phase-1)

## Problem Statement

**FACT (Not Opinion)**: `sys_claim` was performing idempotency handling BEFORE deterministic arbitration.

### What Was Broken

```python
# BROKEN ORDER (before fix):
Step 1: Allocate audit root
Step 2: Idempotency CAS check  ← TOO EARLY
  if not claimed → return HTTP 200 REPLAY
Step 3: Physical resource claim (never reached by concurrent requests)
```

**Result**: All concurrent requests hit idempotency check, second+ requests return HTTP 200 REPLAY immediately, short-circuiting arbitration entirely.

**Violation**: "Single Correct Outcome" kernel law - multiple requests appeared successful when only one should win.

## Solution

### Fixed Execution Order

```python
# CORRECT ORDER (after fix):
Step 1: Allocate audit root
Step 2: Deterministic arbitration  ← MOVED HERE
  if LOSE → return HTTP 409 CONFLICT immediately
Step 3: Idempotency CAS check (ONLY for arbitration winner)
  if first claim → proceed to resource claim
  if replay with status==SUCCEEDED → return HTTP 200 REPLAY
  if replay with other status → return HTTP 409 CONFLICT
Step 4: Physical resource claim
```

### Deterministic Arbitration Algorithm

**Rule**: Winner = smallest SHA256(f"{context_hash}:{owner_id}")

**Window**: 2-second epoch buckets (deterministic time quantization)

**Process**:
1. Compute time bucket: `bucket = epoch_seconds // 2`
2. Query `KernelAuditLog` for concurrent `SYS_CLAIM` on same resource in same bucket
3. Compute arbitration hash for each request (including current)
4. Sort by hash, smallest wins
5. Return `is_winner=True/False`

**No Randomness**: Pure deterministic selection based on hash comparison

**No Arrival-Time Logic**: Only time bucket matters, not exact microsecond timing

## Implementation Details

### New Helper Functions

**`_compute_arbitration_hash(context_hash, owner_id) -> str`**
- Computes SHA256(f"{context_hash}:{owner_id}")
- Returns hex digest for comparison

**`_compute_time_bucket(timestamp, window_seconds=2) -> int`**
- Quantizes timestamp into 2-second epoch buckets
- Returns bucket ID: `int(epoch_seconds) // 2`

**`_run_deterministic_arbitration(...) -> (bool, str)`**
- Queries `KernelAuditLog` for concurrent attempts
- Filters by: `event_type='SYS_CLAIM'`, same `resource_type/resource_id`, same time bucket
- Computes hash for each, sorts, determines winner
- Returns `(is_winner, reason)` tuple

### Changes to sys_claim()

**Before** (lines ~353-363):
```python
# Step 2: Idempotency CAS
idempotency_key = f"sys_claim:{decision_id}:{context_hash}"
claimed, idempotency_record = claim_idempotency_key(...)

if not claimed:
    # Return REPLAY immediately
    return SyscallResult(...)
```

**After** (lines ~394-447):
```python
# Step 2: Deterministic Arbitration (BEFORE idempotency)
is_winner, arbitration_reason = _run_deterministic_arbitration(
    context_hash=context_hash,
    owner_id=owner_id,
    resource_type=resource_type,
    resource_id=resource_id,
    current_time=timezone.now(),
)

if not is_winner:
    # Arbitration loser - return CONFLICT immediately
    outcome = classify_failure(
        KernelErrorCode.CONFLICT,
        f"Arbitration loser: {arbitration_reason}",
    )
    return SyscallResult(...)  # HTTP 409

# Step 3: Idempotency CAS (ONLY for winner)
claimed, idempotency_record = claim_idempotency_key(...)
# ... rest of logic
```

## HTTP Status Code Mapping

**Before Fix**:
- Request A (first): HTTP 200 OK ✅
- Request B (concurrent, different context): HTTP 200 REPLAY ❌ WRONG

**After Fix**:
- Request A (arbitration winner): HTTP 200 OK ✅
- Request B (arbitration loser): HTTP 409 CONFLICT ✅ CORRECT
- Request C (replay of A with status=SUCCEEDED): HTTP 200 REPLAY ✅
- Request D (replay of A with status=IN_PROGRESS): HTTP 409 CONFLICT ✅

## Verification

### Expected simulate_rogue.py Results

**Attack A** (multi-context, same resource):
```
Expected: 1 × HTTP 200 OK, (N-1) × HTTP 409 CONFLICT
```

**Attack B** (same context, different owner):
```
Expected: 1 × HTTP 200 OK, (N-1) × HTTP 409 CONFLICT
(or 1 × 200 + (N-1) × 200 REPLAY if truly identical context_hash)
```

**No "all REPLAY" scenarios** - this was the bug signature

### Test Command

```bash
python3 gateai/scripts/simulate_rogue.py
```

**Success Criteria**:
- Exactly 1 HTTP 200 per resource per time bucket (winner only)
- All other concurrent requests: HTTP 409 CONFLICT
- No HTTP 200 REPLAY for different context_hash requests

## Compliance with Kernel Laws

✅ **Minimal Diff**: Only changed `syscalls.py`, added 3 helper functions, reordered steps

✅ **Determinism**: SHA256 hash comparison, no randomness, no arrival-time logic

✅ **No Feature Injection**: Pure bug fix, no new features

✅ **Explicit Arbitration**: Winner selection rule is explicit and auditable

✅ **Safety First**: Losers correctly rejected with HTTP 409, no false success

✅ **No Refactoring**: Preserved all existing logging, audit, error handling

✅ **Stdlib Only**: Used hashlib (stdlib), no new dependencies

✅ **Did Not Touch**: `idempotency_primitives.py`, `models.py`, application layer

## Files Changed

### gateai/kernel/syscalls.py

**Additions**:
- Import `hashlib` (line 22)
- Add `Tuple` to typing imports (line 24)
- `_compute_arbitration_hash()` function (lines ~225-237)
- `_compute_time_bucket()` function (lines ~240-253)
- `_run_deterministic_arbitration()` function (lines ~256-340)

**Modifications**:
- `sys_claim()` docstring: Updated behavior description (lines ~392-399)
- `sys_claim()` body: Added arbitration step before idempotency (lines ~394-447)
- Updated step numbers in comments (Step 2→3, Step 3→4, etc.)

**Lines Changed**: ~130 lines added/modified (minimal diff achieved)

## Architecture Notes

### Why Query KernelAuditLog?

- Every `sys_claim` allocates audit root FIRST (before arbitration or idempotency)
- Audit log provides complete view of ALL concurrent attempts (winners and losers)
- Filters by `event_type='SYS_CLAIM'`, `resource_type`, `resource_id`, time bucket
- Deterministic: same query inputs → same results

### Why 2-Second Buckets?

- Balances fairness with throughput
- Prevents microsecond arrival-time races
- Allows reasonable concurrent load (multiple buckets per second in high-load scenarios)
- Deterministic: same timestamp → same bucket

### Why SHA256(context_hash:owner_id)?

- `context_hash`: Captures semantic intent of request
- `owner_id`: Distinguishes different actors with same intent
- SHA256: Cryptographically secure, uniformly distributed
- Deterministic: same inputs → same hash → same winner

### Fail-Open Strategy

On arbitration query exception:
- Default to `is_winner=True` (allow request)
- Logs error for monitoring
- Rationale: Availability over perfect arbitration (graceful degradation)

## Migration Notes

**No Database Changes**: No schema changes, no migrations required

**Backward Compatible**: Existing behavior preserved for single-request scenarios

**Performance Impact**: +1 query to `KernelAuditLog` per `sys_claim` (indexed on `event_type`, `created_at`)

**Rollback**: Simply revert `syscalls.py` changes

## Next Steps (Phase-2, if needed)

Potential optimizations (NOT in scope for minimal diff):

1. **Arbitration Cache**: Cache arbitration results for same bucket
2. **Dedicated Arbitration Table**: Separate table for pending claims (avoid KernelAuditLog scan)
3. **Adaptive Bucket Size**: Adjust window based on load
4. **Early Exit**: Stop querying once winner determined

**DO NOT IMPLEMENT THESE NOW** - they violate minimal diff requirement

## Summary

✅ **Problem Fixed**: Arbitration now runs BEFORE idempotency  
✅ **Single Winner**: Only arbitration winner proceeds to resource claim  
✅ **Deterministic**: SHA256 hash comparison, 2-second buckets, no randomness  
✅ **Minimal Diff**: Only changed `syscalls.py`, 3 new functions, reordered steps  
✅ **Kernel Laws**: Compliant with all constraints  
✅ **HTTP Codes**: 200 for winner/safe-replay only, 409 for losers/unsafe-replay  

**Status**: ✅ READY FOR VERIFICATION

Run `python3 gateai/scripts/simulate_rogue.py` to verify fix.

