# ABI Freeze — Pulse v0.1

**Date**: 2026-01-14  
**Status**: 🔒 FROZEN  
**Contract Version**: v0.1  
**Backward Compatibility**: REQUIRED

---

## Overview

Pulse ABI v0.1 is the **frozen contract** for the Kernel Pulse observability plane. This document defines the immutable interface that MUST be maintained for all future v0.x releases.

### Stability Guarantee

- ✅ **v0.1 → v0.2+**: All v0.1 fields MUST remain present and compatible
- ✅ **Additive Only**: New fields MAY be added (non-breaking)
- ❌ **No Removals**: Existing fields MUST NOT be removed
- ❌ **No Type Changes**: Field types MUST NOT change
- ❌ **No Semantic Changes**: Field meanings MUST NOT change

---

## Pulse ABI v0.1 Contract

### Endpoint

```
GET /kernel/pulse/summary/
```

**Authentication**: Required (JWT Bearer token)  
**Authorization**: SuperAdmin + Kernel World Only  
**Content-Type**: `application/json`

---

### Response Schema (JSON)

```json
{
  "pulse_version": "0.1",
  "now": "2026-01-14T12:00:00.000000Z",
  "kernel_state": {
    "mode": "NORMAL",
    "active_lock_pressure": "LOW",
    "error_rate_1h": 0.0234,
    "chaos_safe": true
  },
  "recent_syscalls": [
    {
      "at": "2026-01-14T11:59:58.123456Z",
      "syscall": "SYS_CLAIM",
      "decision_slot_id": "slot_uuid_or_string",
      "outcome": "SUCCESS",
      "error_code": null,
      "trace_id": "event_uuid",
      "resource_type": null,
      "resource_id": null,
      "owner_id": null
    }
  ],
  "counts": {
    "last_1h": {
      "total": 150,
      "success": 145,
      "retryable": 3,
      "terminal": 1,
      "conflict": 1
    },
    "last_24h": {
      "total": 3200,
      "success": 3150,
      "retryable": 30,
      "terminal": 15,
      "conflict": 5
    }
  },
  "active_locks": {
    "count": 5,
    "samples": [
      {
        "resource_type": "TIMESLOT",
        "resource_id": "slot_123",
        "owner_id": "user_456",
        "expires_at": "2026-01-14T12:05:00.000000Z",
        "status": "LOCKED"
      }
    ]
  },
  "top_errors_24h": [
    {
      "error_code": "LOCK_CONFLICT",
      "count": 25
    }
  ]
}
```

---

## Field Specifications

### Top-Level Fields

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `pulse_version` | string | ✅ Yes | ABI version, must be `"0.1"` | 🔒 |
| `now` | string (ISO8601) | ✅ Yes | Current server timestamp | 🔒 |
| `kernel_state` | object | ✅ Yes | Kernel health state | 🔒 |
| `recent_syscalls` | array | ✅ Yes | Last 20 syscalls (may be empty) | 🔒 |
| `counts` | object | ✅ Yes | Syscall aggregates | 🔒 |
| `active_locks` | object | ✅ Yes | Current resource locks | 🔒 |
| `top_errors_24h` | array | ✅ Yes | Most common errors (may be empty) | 🔒 |

---

### `kernel_state` Object

| Field | Type | Required | Values | Description | Frozen v0.1 |
|-------|------|----------|--------|-------------|-------------|
| `mode` | string | ✅ Yes | `NORMAL`, `DEGRADED`, `LOCKED` | Kernel operating mode | 🔒 |
| `active_lock_pressure` | string | ✅ Yes | `LOW`, `MEDIUM`, `HIGH` | Resource lock pressure | 🔒 |
| `error_rate_1h` | number | ✅ Yes | 0.0 to 1.0 | Error rate (last 1 hour) | 🔒 |
| `chaos_safe` | boolean | ✅ Yes | true/false | Safe for chaos engineering | 🔒 |

**Derivation Rules** (FROZEN):
```python
# Mode
if error_rate_1h < 0.05:
    mode = "NORMAL"
elif error_rate_1h < 0.2:
    mode = "DEGRADED"
else:
    mode = "LOCKED"

# Lock Pressure
if active_locks < 10:
    pressure = "LOW"
elif active_locks < 100:
    pressure = "MEDIUM"
else:
    pressure = "HIGH"

# Chaos Safety
chaos_safe = (mode != "LOCKED")
```

---

### `recent_syscalls` Array

**Item Schema**:

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `at` | string (ISO8601) | ✅ Yes | Syscall timestamp | 🔒 |
| `syscall` | string | ✅ Yes | Syscall name (e.g., "SYS_CLAIM") | 🔒 |
| `decision_slot_id` | string\|null | ✅ Yes | Associated decision slot ID | 🔒 |
| `outcome` | string | ✅ Yes | See Outcome Values below | 🔒 |
| `error_code` | string\|null | ✅ Yes | Error code if failed | 🔒 |
| `trace_id` | string\|null | ✅ Yes | Trace/event ID | 🔒 |
| `resource_type` | string\|null | ✅ Yes | Resource type (if applicable) | 🔒 |
| `resource_id` | string\|null | ✅ Yes | Resource ID (if applicable) | 🔒 |
| `owner_id` | string\|null | ✅ Yes | Owner ID (if applicable) | 🔒 |

**Outcome Values** (FROZEN):
- `SUCCESS` - Syscall completed successfully
- `FAILED_RETRYABLE` - Syscall failed, retryable
- `FAILED_TERMINAL` - Syscall failed, terminal
- `CONFLICT` - Syscall rejected due to conflict

**Ordering**: Most recent first (DESC by `at`)  
**Limit**: 20 items maximum

---

### `counts` Object

**Structure**:

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `last_1h` | object | ✅ Yes | Counts for last 1 hour | 🔒 |
| `last_24h` | object | ✅ Yes | Counts for last 24 hours | 🔒 |

**Count Object Schema**:

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `total` | integer | ✅ Yes | Total syscalls | 🔒 |
| `success` | integer | ✅ Yes | Successful syscalls | 🔒 |
| `retryable` | integer | ✅ Yes | Retryable failures | 🔒 |
| `terminal` | integer | ✅ Yes | Terminal failures | 🔒 |
| `conflict` | integer | ✅ Yes | Conflict rejections | 🔒 |

**Invariant**: `total = success + retryable + terminal + conflict`

---

### `active_locks` Object

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `count` | integer | ✅ Yes | Total active locks | 🔒 |
| `samples` | array | ✅ Yes | Sample of active locks (≤10) | 🔒 |

**Lock Sample Schema**:

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `resource_type` | string | ✅ Yes | Type of locked resource | 🔒 |
| `resource_id` | string | ✅ Yes | ID of locked resource | 🔒 |
| `owner_id` | string\|null | ✅ Yes | Lock owner ID | 🔒 |
| `expires_at` | string (ISO8601)\|null | ✅ Yes | Lock expiration time | 🔒 |
| `status` | string | ✅ Yes | Lock status | 🔒 |

**Active Lock Definition** (FROZEN):
```python
status = "active" AND (expires_at IS NULL OR expires_at > now)
```

---

### `top_errors_24h` Array

**Item Schema**:

| Field | Type | Required | Description | Frozen v0.1 |
|-------|------|----------|-------------|-------------|
| `error_code` | string | ✅ Yes | Error code or message | 🔒 |
| `count` | integer | ✅ Yes | Occurrence count | 🔒 |

**Ordering**: DESC by `count`  
**Limit**: 10 items maximum  
**Filter**: Non-null, non-empty error codes only  
**Timeframe**: Last 24 hours

---

## Invariants (FROZEN)

### Safety Invariants

1. **READ-ONLY**: Endpoint MUST NOT modify any database state
2. **NO SIDE EFFECTS**: No background jobs, webhooks, or external calls
3. **DB-NATIVE**: All data MUST come from database queries only
4. **KERNEL-ONLY**: Endpoint MUST be protected by Kernel GovernanceMiddleware
5. **SUPERUSER-ONLY**: Endpoint MUST require `is_superuser=true`

### Performance Invariants

1. **Response Time**: Target < 500ms (p95)
2. **Query Limits**: 
   - `recent_syscalls`: 20 items max
   - `active_locks.samples`: 10 items max
   - `top_errors_24h`: 10 items max
3. **No Pagination**: All data returned in single response (v0.1)

### Data Invariants

1. **Timestamps**: MUST be ISO8601 format with timezone (Z suffix)
2. **Nullability**: Null fields MUST be explicit `null`, not omitted
3. **Empty Arrays**: Empty arrays MUST be `[]`, not omitted
4. **Count Consistency**: `counts.*.total` MUST equal sum of components

---

## Backward Compatibility Rules

### Allowed Changes (Non-Breaking)

✅ **Add new top-level field** (e.g., `kernel_metrics`)
```json
{
  "pulse_version": "0.2",
  "now": "...",
  "kernel_state": {...},
  "kernel_metrics": {...}  // NEW in v0.2
}
```

✅ **Add new field to existing object** (e.g., `kernel_state.uptime_seconds`)
```json
{
  "kernel_state": {
    "mode": "NORMAL",
    "active_lock_pressure": "LOW",
    "error_rate_1h": 0.0,
    "chaos_safe": true,
    "uptime_seconds": 86400  // NEW in v0.2
  }
}
```

✅ **Add new enum value** (with backward compat)
```json
{
  "kernel_state": {
    "mode": "RECOVERY"  // NEW in v0.2 (clients ignore unknown)
  }
}
```

✅ **Extend array items** (add new fields)
```json
{
  "recent_syscalls": [
    {
      "at": "...",
      "syscall": "...",
      "latency_ms": 123  // NEW in v0.2
    }
  ]
}
```

### Forbidden Changes (Breaking)

❌ **Remove any field**
```json
// BREAKING: missing error_rate_1h
{
  "kernel_state": {
    "mode": "NORMAL",
    "active_lock_pressure": "LOW",
    "chaos_safe": true
  }
}
```

❌ **Change field type**
```json
// BREAKING: error_rate_1h changed from number to string
{
  "kernel_state": {
    "error_rate_1h": "2.34%"
  }
}
```

❌ **Change field meaning**
```json
// BREAKING: mode now means "deployment mode" instead of "health mode"
{
  "kernel_state": {
    "mode": "PRODUCTION"
  }
}
```

❌ **Change null semantics**
```json
// BREAKING: owner_id no longer nullable
{
  "active_locks": {
    "samples": [
      {"owner_id": ""}  // Should be null
    ]
  }
}
```

---

## Version Evolution

### v0.1 (Current) 🔒

- **Status**: FROZEN
- **Release**: 2026-01-14
- **Breaking Changes**: N/A (initial release)

### v0.2 (Future)

- **Status**: Planned
- **Compatibility**: MUST include all v0.1 fields
- **Potential Additions**:
  - `kernel_metrics` top-level field
  - `kernel_state.uptime_seconds`
  - `recent_syscalls[].latency_ms`
  - Pagination support (opt-in via query param)

### v1.0 (Future)

- **Status**: Proposal
- **Breaking Changes**: Allowed (major version bump)
- **Migration Path**: v0.x → v1.0 adapter layer required

---

## Compliance Verification

### Automated Tests

```bash
# Run ABI compliance tests
cd gateai
python3 manage.py test kernel.pulse.test_pulse --settings=gateai.settings_test
```

**Required Tests**:
- ✅ All top-level keys present
- ✅ All nested keys present
- ✅ Field types correct
- ✅ Enum values valid
- ✅ Null handling correct
- ✅ Array limits respected

### Manual Verification

```bash
# Get ABI response
export TOKEN="..."
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/ | jq

# Validate against schema (future)
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/ | \
     ajv validate -s docs/pulse_abi_v0_1_schema.json
```

---

## Client Recommendations

### Robust Parsing

```typescript
// Good: Defensive parsing with defaults
const pulse = response.data;
const mode = pulse?.kernel_state?.mode || 'UNKNOWN';
const errorRate = pulse?.kernel_state?.error_rate_1h ?? 0;

// Good: Handle new fields gracefully
const uptime = pulse?.kernel_state?.uptime_seconds; // May be undefined in v0.1
if (uptime !== undefined) {
  console.log(`Uptime: ${uptime}s`);
}

// Bad: Strict parsing (breaks on additions)
const { mode, active_lock_pressure, error_rate_1h, chaos_safe } = pulse.kernel_state;
// ❌ Will throw if new fields added in v0.2
```

### Version Detection

```typescript
// Check pulse_version
if (pulse.pulse_version === '0.1') {
  // v0.1 logic
} else if (pulse.pulse_version === '0.2') {
  // v0.2 logic (with v0.1 fallbacks)
} else {
  console.warn(`Unknown Pulse ABI version: ${pulse.pulse_version}`);
}
```

---

## Change Log

| Version | Date | Changes | Breaking |
|---------|------|---------|----------|
| v0.1 | 2026-01-14 | Initial release | N/A |

---

## References

- Implementation: `gateai/kernel/pulse/views.py`
- Tests: `gateai/kernel/pulse/test_pulse.py`
- Acceptance: `docs/PHASE_A1_ACCEPTANCE_TESTS.md`
- Smoke Tests: `docs/PHASE_A1_SUPERADMIN_SMOKE.md`

---

**Pulse ABI v0.1**  
**Status**: 🔒 FROZEN  
**Stability**: GUARANTEED  
**Date**: 2026-01-14
