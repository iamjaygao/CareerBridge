# PATCH — Bus Grouped Workload Registry v0.2

**Date**: 2026-01-14  
**Status**: ✅ COMPLETE  
**Issue**: Frontend crash due to schema mismatch (array vs object)

---

## Problem

Frontend `WorkloadRuntimeConsolePage` was crashing with:
```
TypeError: Object.entries(undefined)
```

**Root Cause**: Registry schema mismatch
- Scanner output: `buses: [ ... ]` (array)
- Frontend expected: `buses: { PAYMENT_BUS: {...}, AI_BUS: {...} }` (object)

---

## Solution

Upgraded registry schema from **array-based** to **object-based** buses without touching backend logic.

### Schema Change

**Before (v0.2 array)**:
```json
{
  "version": "0.2",
  "buses": [
    {
      "bus": "AI_BUS",
      "status": "FROZEN",
      "reason": "Phase-A freeze",
      "workloads": [...]
    }
  ]
}
```

**After (v0.2 object)**:
```json
{
  "version": "0.2",
  "buses": {
    "AI_BUS": {
      "state": "OFF",
      "workloads": [...]
    },
    "PAYMENT_BUS": {
      "state": "OFF",
      "workloads": [...]
    },
    "KERNEL_CORE_BUS": {
      "state": "ON",
      "workloads": [...]
    }
  }
}
```

### Key Changes

1. **Buses as Object**: `buses: []` → `buses: {}`
2. **State Field**: `status: "FROZEN"` → `state: "ON"/"OFF"`
3. **Removed Fields**: `bus` (redundant, now key), `status`, `reason`
4. **KERNEL_CORE_BUS**: `state: "ON"` (only powered bus)

---

## Files Changed

### Modified (3)
1. `scripts/build_frozen_registry.mjs` — Changed output to object-based buses
2. `frontend/src/pages/superadmin/WorkloadRuntimeConsolePage.tsx` — Rewritten for object schema
3. `frontend/src/pages/superadmin/__tests__/WorkloadRuntimeConsolePage.test.tsx` — Updated tests

---

## How to Apply Patch

```bash
# Step 1: Regenerate registry with new schema
node scripts/build_frozen_registry.mjs

# Step 2: Sync to frontend
./scripts/sync_registry_to_frontend.sh

# Step 3: Restart frontend
cd frontend && npm start

# Step 4: Verify
# Navigate to: http://localhost:3000/superadmin/workload-runtime
# Should load without crash, display buses with ON/OFF state
```

---

## Acceptance Criteria

✅ Frontend `/superadmin/workload-runtime` loads without crash  
✅ Workloads grouped by BUS (object keys)  
✅ Each bus shows `state: "ON"` or `state: "OFF"`  
✅ KERNEL_CORE_BUS shows `state: "ON"`  
✅ All other buses show `state: "OFF"`  
✅ No backend API calls made (only static registry)  
✅ Click bus to expand workloads  

---

## Registry Output Example

```json
{
  "version": "0.2",
  "generated_at": "2026-01-14T03:01:05.096Z",
  "scan_summary": {
    "total_workloads": 32,
    "total_buses": 8,
    "by_bus": {
      "ADMIN_BUS": 2,
      "AI_BUS": 14,
      "KERNEL_CORE_BUS": 1,
      "MENTOR_BUS": 7,
      "PAYMENT_BUS": 1,
      "PUBLIC_WEB_BUS": 3,
      "SEARCH_BUS": 1,
      "UNKNOWN_BUS": 3
    }
  },
  "buses": {
    "ADMIN_BUS": {
      "state": "OFF",
      "workloads": [ ... ]
    },
    "AI_BUS": {
      "state": "OFF",
      "workloads": [ ... ]
    },
    "KERNEL_CORE_BUS": {
      "state": "ON",
      "workloads": [ ... ]
    },
    ...
  }
}
```

---

## Bus State Mapping

| Bus | State | Reason |
|-----|-------|--------|
| KERNEL_CORE_BUS | **ON** | Kernel must be accessible |
| PAYMENT_BUS | OFF | Phase-A freeze |
| MENTOR_BUS | OFF | Phase-A freeze |
| AI_BUS | OFF | Phase-A freeze |
| ADMIN_BUS | OFF | Phase-A freeze |
| PUBLIC_WEB_BUS | OFF | Phase-A freeze |
| SEARCH_BUS | OFF | Phase-A freeze |
| UNKNOWN_BUS | OFF | Phase-A freeze |

---

## Deterministic Bus Classification

Rules (applied in scanner):

```javascript
// Rule 1: Kernel world → KERNEL_CORE_BUS
if (workload.world === "kernel" || workload.name.includes("kernel")) {
  return "KERNEL_CORE_BUS";
}

// Rule 2: Payment keywords → PAYMENT_BUS
if (["payments", "stripe", "billing"].includes(workload.name)) {
  return "PAYMENT_BUS";
}

// Rule 3: Mentor keywords → MENTOR_BUS
if (["mentor", "appointments", "human_loop"].includes(workload.name)) {
  return "MENTOR_BUS";
}

// Rule 4: AI keywords → AI_BUS
if (["ai", "engine", "ats", "signal"].includes(workload.name)) {
  return "AI_BUS";
}

// Rule 5: Admin world → ADMIN_BUS
if (workload.world === "admin") {
  return "ADMIN_BUS";
}

// Rule 6: Search → SEARCH_BUS
if (["search", "analytics"].includes(workload.name)) {
  return "SEARCH_BUS";
}

// Rule 7: Public world → PUBLIC_WEB_BUS
if (workload.world === "app" && ["public", "landing", "pricing"].includes(workload.name)) {
  return "PUBLIC_WEB_BUS";
}

// Fallback: UNKNOWN_BUS
return "UNKNOWN_BUS";
```

---

## Frontend Changes

### Interface Updates

**Before**:
```typescript
interface Bus {
  bus: string;
  status: string;
  reason: string;
  workloads: Workload[];
}

interface Registry {
  buses: Bus[];  // Array
}
```

**After**:
```typescript
interface BusData {
  state: 'ON' | 'OFF';
  workloads: Workload[];
}

interface Registry {
  buses: Record<string, BusData>;  // Object
}
```

### Rendering Logic

**Before**:
```typescript
registry.buses.map((bus) => (
  <TableRow key={bus.bus}>
    <TableCell>{bus.bus}</TableCell>
    <TableCell>{bus.status}</TableCell>
  </TableRow>
))
```

**After**:
```typescript
Object.entries(registry.buses).map(([busId, busData]) => (
  <TableRow key={busId}>
    <TableCell>{busId}</TableCell>
    <TableCell>{busData.state}</TableCell>
  </TableRow>
))
```

---

## Testing

### Updated Tests

```typescript
// Test: buses as object (not array)
const mockRegistry = {
  version: '0.2',
  buses: {                    // Object, not array
    AI_BUS: {
      state: 'OFF',           // state, not status
      workloads: [...]
    }
  }
};
```

### Run Tests

```bash
cd frontend
npm test -- WorkloadRuntimeConsolePage.test.tsx
```

**Expected**: All tests pass

---

## Benefits of Object-Based Schema

1. **Direct Lookup**: `buses.PAYMENT_BUS` vs `buses.find(b => b.bus === 'PAYMENT_BUS')`
2. **Cleaner API**: No redundant `bus` field (it's the key)
3. **State Clarity**: `state: "ON"/"OFF"` is more explicit than `status: "FROZEN"`
4. **Alignment with Bus Power**: Matches `bus_power.py` structure

---

## Status

**Patch**: ✅ APPLIED  
**Tests**: ✅ UPDATED  
**Frontend**: ✅ FIXED  
**Registry**: ✅ REGENERATED  

**Ready for**: Production use

---

**Delivered**: 2026-01-14  
**Patch**: Bus Grouped Registry v0.2 (Object-based)
