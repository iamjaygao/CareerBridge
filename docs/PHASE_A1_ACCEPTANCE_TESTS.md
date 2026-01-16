# Phase-A.1 Kernel Pulse — Acceptance Tests

**Status**: ✅ Implementation Complete  
**Pulse ABI**: v0.1 (Frozen)  
**Date**: 2026-01-14

---

## Quick Start

### 1. Get JWT Token

```bash
# Login as SuperAdmin
curl -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"YOUR_SUPERUSER_USERNAME","password":"YOUR_PASSWORD"}'
```

**Extract the `access` token from response:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "...",
  "user": {...}
}
```

### 2. Export Token

```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Run Verification Script

```bash
./scripts/verify_kernel_pulse.sh
```

**Expected Output:**

```
╔════════════════════════════════════════════════════════════╗
║     Phase-A.1 Kernel Pulse — Acceptance Verification      ║
╚════════════════════════════════════════════════════════════╝

🔑 Token: eyJhbGciOiJIUzI1NiIs...

📡 GET http://localhost:8001/kernel/pulse/summary/

✅ HTTP 200 OK
✅ Valid JSON

🔍 Validating Pulse ABI v0.1 contract...

  ✅ pulse_version
  ✅ now
  ✅ kernel_state
  ✅ recent_syscalls
  ✅ counts
  ✅ active_locks
  ✅ top_errors_24h
  ✅ .kernel_state.mode
  ✅ .kernel_state.active_lock_pressure
  ✅ .kernel_state.error_rate_1h
  ✅ .kernel_state.chaos_safe
  ✅ .counts.last_1h
  ✅ .counts.last_24h
  ✅ .active_locks.count
  ✅ .active_locks.samples

─────────────────────────────────────────────────────────────
Checks: 15 passed, 0 failed
─────────────────────────────────────────────────────────────

✅ pulse_version: 0.1

📊 Kernel State Summary:
────────────────────────────────────────────────────────────
  Mode:          NORMAL
  Lock Pressure: LOW
  Error Rate:    0.0
  Chaos Safe:    true

📈 Activity Summary:
────────────────────────────────────────────────────────────
  Last 1h:  0 syscalls (0 success)
  Last 24h: 0 syscalls

🔒 Active Locks: 0
⚠️  Top Errors:   0 unique error types

╔════════════════════════════════════════════════════════════╗
║              ✅ Phase-A.1 Acceptance: PASSED              ║
╚════════════════════════════════════════════════════════════╝
```

---

## Manual curl Test

If you prefer manual testing:

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/ | jq
```

---

## Expected Top-Level ABI Keys

Pulse ABI v0.1 **MUST** contain these top-level keys:

1. **`pulse_version`** (string) - Must be `"0.1"`
2. **`now`** (ISO8601 string) - Current timestamp
3. **`kernel_state`** (object) - Kernel health metrics
   - `mode`: `"NORMAL"` | `"DEGRADED"` | `"LOCKED"`
   - `active_lock_pressure`: `"LOW"` | `"MEDIUM"` | `"HIGH"`
   - `error_rate_1h`: float (0.0 to 1.0)
   - `chaos_safe`: boolean
4. **`recent_syscalls`** (array) - Last 20 kernel events
5. **`counts`** (object) - Syscall aggregates
   - `last_1h`: {total, success, retryable, terminal, conflict}
   - `last_24h`: {total, success, retryable, terminal, conflict}
6. **`active_locks`** (object) - Current resource locks
   - `count`: integer
   - `samples`: array (up to 10 locks)
7. **`top_errors_24h`** (array) - Most common errors

---

## Acceptance Criteria

Phase-A.1 is **ACCEPTED** when:

- ✅ `./scripts/verify_kernel_pulse.sh` exits with code 0
- ✅ All 15 ABI key checks pass
- ✅ `pulse_version` is exactly `"0.1"`
- ✅ Response is valid JSON
- ✅ HTTP status is 200 OK

---

## Troubleshooting

### Error: "TOKEN not set"

```bash
export TOKEN="YOUR_JWT_TOKEN_HERE"
```

### Error: HTTP 403 Forbidden

**Cause**: Token is invalid, expired, or user is not a SuperAdmin.

**Fix**:
```bash
# Get a fresh token
curl -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"SUPERUSER","password":"PASSWORD"}' | jq -r '.access'

# Export it
export TOKEN="NEW_TOKEN"
```

### Error: HTTP 404 Not Found

**Cause**: Backend not running or wrong URL.

**Fix**:
```bash
# Start backend
cd gateai
python3 manage.py runserver 8001

# Verify URL
echo $BACKEND_URL  # Should be http://localhost:8001
```

### Error: "jq: command not found"

**macOS**:
```bash
brew install jq
```

**Ubuntu/Debian**:
```bash
sudo apt-get install jq
```

**Without jq**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/
```

---

## Next Steps

After passing acceptance tests:

1. ✅ Run SuperAdmin smoke tests (see `docs/PHASE_A1_SUPERADMIN_SMOKE.md`)
2. ✅ Review ABI freeze documentation (see `docs/ABI_FREEZE_PULSE_v0_1.md`)
3. 🚀 Deploy to staging
4. 📊 Monitor kernel pulse metrics
5. 🏷️ Tag release: `pulse-abi-v0.1`

---

**Phase-A.1 Kernel Pulse**  
**Acceptance Gate**: ✅ Ready for Validation  
**Date**: 2026-01-14
