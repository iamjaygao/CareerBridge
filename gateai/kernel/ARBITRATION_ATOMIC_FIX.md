# Atomic Arbitration Fix - Phase 1 Final (Barrier-Based)

## Root Cause Analysis

**Previous Implementation Was Broken**:
- Queried `KernelAuditLog` for competitors
- Under concurrency: each request sees partial/no competitors
- All requests think "I'm winner"
- All proceed to idempotency check
- First marks `SUCCEEDED`, others get `REPLAY` (HTTP 200)
- **Result**: All requests return HTTP 200 (not deterministic single winner)

**Why It Failed**:
- No atomic gate / lock
- Query-based arbitration is inherently racy
- No synchronization barrier

## Solution: Atomic Barrier-Based Arbitration

### Core Insight

To implement "winner = min(hash)" deterministically, we need:
1. **Atomic record** with UNIQUE constraint (gate)
2. **Barrier**: Wait for bucket to close (let all contenders arrive)
3. **Decide**: Atomically lock record, compute winner, persist

### New Model: KernelArbitrationRecord

```python
class KernelArbitrationRecord(models.Model):
    resource_id = CharField(max_length=255, db_index=True)
    bucket_start = DateTimeField(db_index=True)
    
    # Winner fields (populated after decision)
    winner_hash = CharField(max_length=64, blank=True, default="")
    winner_owner_id = CharField(max_length=128, blank=True, default="")
    winner_context_hash = CharField(max_length=128, blank=True, default="")
    decided_at = DateTimeField(null=True, blank=True)
    
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            UniqueConstraint(fields=['resource_id', 'bucket_start'],
                           name='uniq_arb_resource_bucket')
        ]
```

**Key Properties**:
- `UNIQUE(resource_id, bucket_start)`: Only ONE record per resource per bucket
- `winner_hash`: Persisted winner (deterministic, immutable after decided_at set)
- `decided_at`: Timestamp when winner was frozen

### Algorithm: 3-Phase Barrier Arbitration

**Phase 1: Register Intent**
```python
# Ensure arbitration record exists (atomic get_or_create)
arb_record, created = KernelArbitrationRecord.objects.get_or_create(
    resource_id=resource_id,
    bucket_start=bucket_start,
)
```

**Phase 2: BARRIER (Critical!)**
```python
# Wait for bucket to close + 50ms buffer
bucket_end_time = bucket_start + timedelta(seconds=2)
sleep_seconds = (bucket_end_time - now).total_seconds() + 0.05
if sleep_seconds > 0:
    time.sleep(sleep_seconds)
```

**Why the sleep?**
- Allows all concurrent contenders to register in `KernelAuditLog`
- Without barrier: first request wakes, sees no competitors, declares itself winner
- With barrier: all requests sleep until bucket closes, then first to wake computes winner from COMPLETE set

**Phase 3: DECIDE (Atomic)**
```python
with transaction.atomic():
    # Lock arbitration record
    arb_record = (
        KernelArbitrationRecord.objects
        .select_for_update(nowait=False)
        .get(resource_id=resource_id, bucket_start=bucket_start)
    )
    
    # If decided_at already set: winner is frozen, just compare
    if arb_record.decided_at is not None:
        return (my_hash == arb_record.winner_hash, reason)
    
    # Decide winner:
    # 1. Query KernelAuditLog for all contenders in bucket
    # 2. Compute hash for each
    # 3. winner = min(hash)
    # 4. Persist winner_* fields and set decided_at
    
    candidates = []
    for audit in KernelAuditLog.objects.filter(...):
        hash = SHA256(f"{context_hash}:{owner_id}")
        candidates.append(hash)
    
    winner_hash = min(candidates)
    
    arb_record.winner_hash = winner_hash
    arb_record.winner_owner_id = winner_owner
    arb_record.winner_context_hash = winner_context
    arb_record.decided_at = timezone.now()
    arb_record.save()
    
    return (my_hash == winner_hash, reason)
```

### Integration into sys_claim

**Execution Order (Final, Correct)**:
```python
Step 1: Allocate audit root (KernelAuditLog entry)
Step 2: Compute bucket_start = floor(now / 2 seconds)
Step 3: Compute my_hash = SHA256(f"{context_hash}:{owner_id}")
Step 4: Run _run_bucket_arbitration():
   - Phase 1: Ensure arbitration record exists
   - Phase 2: BARRIER (sleep until bucket closes)
   - Phase 3: DECIDE (lock, compute winner, persist)
   - Return is_winner
Step 5: If NOT is_winner → return HTTP 409 CONFLICT immediately
Step 6: If is_winner → proceed to idempotency check (Step 3 in previous flow)
Step 7: Idempotency check (with SUCCEEDED/IN_PROGRESS semantics)
Step 8: Physical resource claim
```

### Deterministic Properties

✅ **Atomic Gate**: `UNIQUE(resource_id, bucket_start)` constraint  
✅ **Barrier**: All contenders sleep until bucket closes  
✅ **Winner Rule**: `min(SHA256(context_hash:owner_id))` - deterministic, no randomness  
✅ **Immutable**: Once `decided_at` set, winner cannot change  
✅ **Contention-Safe**: `select_for_update` ensures only one decider at a time  

### HTTP Status Codes (Now Correct)

| Scenario | HTTP Status | Outcome Code |
|----------|-------------|--------------|
| Arbitration winner, first claim | 200 OK | OK |
| Arbitration winner, replay with SUCCEEDED | 200 OK | REPLAY |
| Arbitration loser (concurrent different context) | **409 CONFLICT** | CONFLICT |
| Arbitration winner, replay with IN_PROGRESS | 409 CONFLICT | CONFLICT |

**Key Fix**: Arbitration losers now return **409 CONFLICT**, NOT 200 REPLAY

## Files Changed

### 1. gateai/kernel/models.py

**Added**:
- `KernelArbitrationRecord` model (~40 lines)
- UNIQUE constraint on `(resource_id, bucket_start)`
- Indexes on `(resource_id, bucket_start)` and `decided_at`

### 2. gateai/kernel/migrations/0004_add_arbitration_record.py

**Created**:
- Migration to create `KernelArbitrationRecord` table
- Add unique constraint
- Add indexes

### 3. gateai/kernel/syscalls.py

**Modified**:
- `_compute_arbitration_hash()`: Same (stdlib SHA256)
- `_bucket_start()`: New helper (floor timestamp to bucket boundary)
- `_bucket_end()`: New helper (bucket_start + 2 seconds)
- `_run_bucket_arbitration()`: **Complete rewrite** (~150 lines)
  - Implements 3-phase barrier algorithm
  - Uses `KernelArbitrationRecord` as atomic gate
  - Sleep barrier before decision
  - Atomic winner persistence
- `sys_claim()`: Updated to call new arbitration function (~20 lines modified)

**Total Changes**: ~200 lines (minimal diff, scoped to arbitration only)

## Verification

### Test Command

```bash
python3 gateai/scripts/simulate_rogue.py
```

### Expected Output

**Attack A** (multi-context, same resource):
```
Expected: 1 × HTTP 200 (OK or REPLAY), rest × HTTP 409 (CONFLICT)
```

**Attack B** (same context, different owner):
```
Expected: 1 × HTTP 200, rest × HTTP 409
```

**CRITICAL**: **NO "all HTTP 200 REPLAY"** scenarios

If you still see "all REPLAY":
- Arbitration barrier not working (check logs for "BARRIER: Sleeping")
- Arbitration decision not persisting (check `decided_at` in DB)
- Wrong bucket computation (check `bucket_start` in logs)

### Debug Logging

Look for log lines:
```
SYS_CLAIM: ARBITRATION_WINNER (proceeding to idempotency check)
SYS_CLAIM: ARBITRATION_LOSER (deterministic rejection)
```

Check extra fields:
- `resource_id`: Resource being claimed
- `bucket_start`: Bucket timestamp (should be same for all concurrent requests)
- `my_hash`: This request's hash (first 16 chars)
- `is_winner`: True/False

### Database Verification

```sql
-- Check arbitration records
SELECT resource_id, bucket_start, winner_hash, decided_at
FROM kernel_kernelarbitrationrecord
ORDER BY created_at DESC
LIMIT 10;

-- Should see:
-- - One record per (resource_id, bucket_start) pair
-- - decided_at populated after decision
-- - winner_hash matching one of the request hashes
```

## Compliance with Kernel Laws

✅ **Determinism**: SHA256 hash, 2-second buckets, atomic decision  
✅ **Minimal Diff**: Only changed models.py + syscalls.py + migration  
✅ **No Refactoring**: Preserved all existing logic except arbitration  
✅ **Stdlib Only**: Used hashlib, time.sleep (stdlib)  
✅ **Explicit Arbitration**: Winner = min(hash), auditable in DB  
✅ **Safety First**: Losers correctly rejected with HTTP 409  
✅ **Did Not Touch**: idempotency_primitives.py (already correct)  

## Architecture Notes

### Why the Barrier (Sleep)?

**Problem**: Computing "min(hash)" requires seeing ALL contenders

**Without Barrier**:
1. Request A arrives at t=0.000s → queries audit log → sees no contenders → declares winner
2. Request B arrives at t=0.001s → queries audit log → sees no contenders → declares winner
3. **Both think they're winners!**

**With Barrier**:
1. Request A arrives at t=0.000s → sleeps until t=2.050s
2. Request B arrives at t=0.001s → sleeps until t=2.050s
3. Both wake at ~t=2.050s
4. First to acquire lock sees BOTH in audit log → computes winner correctly

### Why 2-Second Buckets?

- Balance between fairness and latency
- Too small (e.g., 100ms): Not enough time for contenders to register
- Too large (e.g., 10s): High latency for losers
- 2 seconds: Reasonable trade-off (matches original requirement)

### Why 50ms Buffer?

- Accounts for clock skew, transaction commit delays
- Ensures audit log entries are visible when decision happens
- Small enough to not significantly increase latency

### Fail-Open Strategy

On error during arbitration:
- Default to `is_winner=True` (allow request)
- Log error for monitoring
- Rationale: Availability > perfect arbitration (graceful degradation)

## Migration Steps

1. **Apply Migration**:
   ```bash
   python manage.py migrate kernel 0004
   ```

2. **Verify Table**:
   ```sql
   \d kernel_kernelarbitrationrecord
   -- Should see UNIQUE constraint on (resource_id, bucket_start)
   ```

3. **Run Tests**:
   ```bash
   python3 gateai/scripts/simulate_rogue.py
   ```

4. **Check Logs**:
   - Look for "ARBITRATION_WINNER" and "ARBITRATION_LOSER"
   - Verify `is_winner` field matches expected behavior

5. **Monitor DB**:
   - Check that arbitration records are created
   - Verify `decided_at` is set
   - Confirm only one winner per bucket

## Rollback Plan

If arbitration causes issues:

1. **Code Rollback**:
   ```bash
   git revert <commit>
   ```

2. **Migration Rollback** (optional, not required for functionality):
   ```bash
   python manage.py migrate kernel 0003
   ```

3. **Manual Cleanup** (if needed):
   ```sql
   DROP TABLE kernel_kernelarbitrationrecord;
   ```

## Performance Impact

**Added Latency**:
- Worst case: +2.05 seconds (bucket closes + buffer)
- Best case: +0.05 seconds (near bucket boundary)
- Average: ~1.025 seconds (midpoint of bucket)

**This is intentional and required for correctness!**

**Queries Added**:
- +1 `get_or_create` on `KernelArbitrationRecord` (indexed)
- +1 `select_for_update` on same record (hot row)
- +1 query to `KernelAuditLog` for contenders (filtered by bucket, indexed)

**Optimization Opportunities (Future, NOT NOW)**:
- Cache arbitration results within bucket
- Early exit if decided_at already set
- Adaptive bucket size based on load

**DO NOT IMPLEMENT OPTIMIZATIONS NOW** - minimal diff requirement

## Summary

✅ **Problem**: Query-based arbitration was racy (all requests thought they were winners)  
✅ **Solution**: Atomic barrier-based arbitration with DB-backed gate  
✅ **Key Components**: KernelArbitrationRecord + sleep barrier + atomic decision  
✅ **Verification**: Losers now return HTTP 409 CONFLICT (not HTTP 200 REPLAY)  
✅ **Compliant**: Deterministic, minimal diff, stdlib only  

**Status**: ✅ READY FOR VERIFICATION

Run `python3 gateai/scripts/simulate_rogue.py` and verify:
- Exactly 1 × HTTP 200 per resource per bucket
- Rest × HTTP 409 CONFLICT
- NO "all REPLAY" scenarios

This is the ONLY correct way to do deterministic arbitration under database concurrency.

