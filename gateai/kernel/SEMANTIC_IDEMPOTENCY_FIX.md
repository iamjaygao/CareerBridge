# Semantic Idempotency Fix - Phase 1

## Problem Statement

**Symptom**: `simulate_rogue.py` shows ALL requests returning HTTP 200 REPLAY, even when requests have different semantic identities (different owners, different contexts).

**Root Cause**: Idempotency key was decision-centric (`sys_claim:{decision_id}:{context_hash}`), not resource-centric. Since each request has a unique `decision_id`, they never collided at the idempotency level, so no semantic collision detection occurred.

## Solution

### 1. Resource-Centric Idempotency Key

**Before** (decision-centric):
```python
idempotency_key = f"sys_claim:{decision_id}:{context_hash}"
```
- Each request gets unique key (unique decision_id)
- No collisions possible
- No semantic mismatch detection

**After** (resource-centric):
```python
idempotency_key = f"sys_claim:{resource_type}:{resource_id}:{context_hash}"
```
- Requests targeting same (resource_type, resource_id, context_hash) share key
- Collisions possible when different owners target same resource
- Enables semantic mismatch detection

### 2. Semantic Identity Definition

**Semantic identity for idempotency replays**:
- SAME `(event_type, context_hash, owner_id)`
- `decision_id` is **NOT** part of semantic identity (informational only)

**Why?**
- `event_type`: Must be same operation type (SYS_CLAIM)
- `context_hash`: Captures the semantic intent of the request
- `owner_id`: WHO is making the request matters for replays
- `decision_id`: Unique per request attempt, not semantic

### 3. Semantic Collision Detection

**Updated** `is_semantically_same_request()`:
```python
def is_semantically_same_request(
    self, event_type: str, context_hash: str, owner_id: str = None
) -> bool:
    """Check semantic identity: (event_type, context_hash, owner_id)"""
    event_match = self.event_type == event_type
    context_match = self.context_hash == context_hash
    
    if owner_id and self.owner_id:
        owner_match = self.owner_id == owner_id
        return event_match and context_match and owner_match
    
    return event_match and context_match
```

**Decision**: `decision_id` removed from check (not semantic)

### 4. Model Changes

**Added field to `KernelIdempotencyRecord`**:
```python
owner_id = models.CharField(max_length=128, blank=True, 
                            help_text="Owner ID for semantic collision detection")
```

**Migration**: `0005_add_owner_id_to_idempotency.py`

### 5. Updated claim_idempotency_key()

**New signature**:
```python
def claim_idempotency_key(
    *,
    idempotency_key: str,
    event_type: str,
    decision_id: str,
    context_hash: str,
    event_id: str = None,
    owner_id: str = None,  # NEW
) -> Tuple[bool, KernelIdempotencyRecord]:
```

**Semantic collision check**:
```python
if not created:
    if not record.is_semantically_same_request(event_type, context_hash, owner_id):
        # COLLISION: same key, different semantic identity
        record.failure_reason = "IDEMPOTENCY_KEY_COLLISION"
        return (False, record)
```

## Expected Behavior

### Attack A: Multi-Context, Same Resource

```python
# Request A: context_hash="hash_A", owner="user1", resource_id=42
# Request B: context_hash="hash_B", owner="user2", resource_id=42

# Different context_hash → different idempotency keys → no collision
# Each proceeds independently
```

### Attack B: Same Context, Different Owner

```python
# Request A: context_hash="shared", owner="user1", resource_id=42
# Request B: context_hash="shared", owner="user2", resource_id=42

# Same context_hash + resource → SAME idempotency key
# Collision at idempotency level!

# Request A (first):
#   - claimed=True, status=IN_PROGRESS
#   - Proceeds to ResourceLock claim
#   - Succeeds → mark_key_succeeded() → status=SUCCEEDED

# Request B (concurrent):
#   - claimed=False (key exists)
#   - is_semantically_same_request? → NO (different owner_id)
#   - failure_reason="IDEMPOTENCY_KEY_COLLISION"
#   - sys_claim returns HTTP 409 CONFLICT
```

### Safe Replay (Identical Request)

```python
# Request A: context_hash="abc", owner="user1", resource_id=42
# Request A' (replay): context_hash="abc", owner="user1", resource_id=42

# Same idempotency key
# Same semantic identity (event_type, context_hash, owner_id)
# Record status=SUCCEEDED
# → sys_claim returns HTTP 200 REPLAY
```

## HTTP Status Code Matrix

| Scenario | Idempotency | Semantic Identity | Status | HTTP | Outcome |
|----------|-------------|------------------|--------|------|---------|
| First request | claimed=True | N/A | IN_PROGRESS→SUCCEEDED | 200 | OK |
| Replay (same owner, same context) | claimed=False | MATCH | SUCCEEDED | 200 | REPLAY |
| Concurrent (diff owner, same context) | claimed=False | MISMATCH | IN_PROGRESS | 409 | CONFLICT |
| Concurrent (diff owner, same context) after winner | claimed=False | MISMATCH | SUCCEEDED | 409 | CONFLICT |

**Key Fix**: Different owner_id → CONFLICT (409), NOT REPLAY (200)

## Integration with sys_claim

```python
# Step 3: Idempotency check (after arbitration)
idempotency_key = f"sys_claim:{resource_type}:{resource_id}:{context_hash}"

claimed, idempotency_record = claim_idempotency_key(
    idempotency_key=idempotency_key,
    event_type="SYS_CLAIM",
    decision_id=decision_id,
    context_hash=context_hash,
    event_id=str(audit.event_id),
    owner_id=str(owner_id),  # Pass for semantic check
)

if not claimed:
    # Check for collision
    if idempotency_record.failure_reason == "IDEMPOTENCY_KEY_COLLISION":
        return HTTP 409 CONFLICT
    
    # Check for safe replay
    if idempotency_record.status in SUCCESS_STATES:
        return HTTP 200 REPLAY  # Same semantic identity, succeeded
    
    # Otherwise: IN_PROGRESS or FAILED
    return HTTP 409 CONFLICT  # Not safe replay
```

## Files Changed

### 1. gateai/kernel/models.py
- Added `owner_id` field to `KernelIdempotencyRecord`
- Updated `is_semantically_same_request()` to check `owner_id` instead of `decision_id`

### 2. gateai/kernel/idempotency_primitives.py
- Added `owner_id` parameter to `claim_idempotency_key()`
- Updated semantic collision check to use `(event_type, context_hash, owner_id)`
- Added self-heal fill for `owner_id` field

### 3. gateai/kernel/syscalls.py
- Changed idempotency key from decision-centric to resource-centric
- Pass `owner_id` to `claim_idempotency_key()`

### 4. gateai/kernel/migrations/0005_add_owner_id_to_idempotency.py
- New migration to add `owner_id` field

### 5. gateai/kernel/tests/test_idempotency_primitives.py
- Updated test for `owner_id` collision detection
- Removed test for `decision_id` collision (no longer semantic)

## Verification

### Run Migration
```bash
cd gateai
python manage.py migrate kernel 0005
```

### Run Tests
```bash
python manage.py test kernel.tests.test_idempotency_primitives
```

### Run Simulation
```bash
python3 scripts/simulate_rogue.py
```

### Expected Results

**Attack A** (multi-context, same resource):
- Different context_hash → different idempotency keys
- Each request proceeds independently
- May still conflict at ResourceLock level (expected)

**Attack B** (same context, different owner):
- Same idempotency key (same context_hash + resource)
- Semantic collision detected (different owner_id)
- Loser requests: HTTP 409 CONFLICT with "IDEMPOTENCY_KEY_COLLISION"
- Winner request: HTTP 200 OK (first to claim)
- **NO more "all HTTP 200 REPLAY"**

### Debug Logs

Look for:
```
ERROR: Idempotency key collision: same key, different operation
  incoming_owner_id: user2
  existing_owner_id: user1

INFO: SYS_CLAIM: Idempotency key collision detected
  → HTTP 409 CONFLICT
```

## Compliance

✅ **No sleep/wait/polling**: Pure database primitives  
✅ **Minimal diff**: Only models.py, idempotency_primitives.py, syscalls.py  
✅ **Stdlib only**: No new dependencies  
✅ **Did not touch arbitration tables**: Arbitration code remains intact  
✅ **Semantic identity definition**: (event_type, context_hash, owner_id)  
✅ **decision_id excluded**: Not part of semantic identity  

## Summary

✅ **Problem**: Decision-centric idempotency keys prevented collision detection  
✅ **Solution**: Resource-centric keys + semantic identity check on owner_id  
✅ **Key Insight**: `decision_id` is per-attempt, not semantic; `owner_id` is semantic  
✅ **Outcome**: Different owners targeting same resource → CONFLICT, not REPLAY  
✅ **Verification**: simulate_rogue.py should show 409 CONFLICT for semantic mismatches  

This fix ensures REPLAY (HTTP 200) is only returned when the request is truly semantically identical to the original winner.

