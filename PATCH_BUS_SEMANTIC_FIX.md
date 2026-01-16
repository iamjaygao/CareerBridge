# PATCH — BUS SEMANTIC FIX (Object Keys vs Array Indices)

**Problem**: Registry schema was outputting numeric-indexed buses destroying capability-domain semantics.

**Root Cause**: Registry was using **array format** (`buses: [...]`) where each array element had a `bus` property, but frontend expected **object format** (`buses: {...}`) where bus IDs are direct object keys.

---

## What Was Fixed

### Before (BROKEN - Array Format)
```json
{
  "buses": [
    {
      "bus": "ADMIN_BUS",
      "status": "FROZEN",
      "workloads": [...]
    },
    {
      "bus": "AI_BUS", 
      "status": "FROZEN",
      "workloads": [...]
    }
  ]
}
```

**Problem**: Frontend code `Object.entries(registry.buses)` would iterate over array indices `["0", "1", "2", ...]` instead of semantic bus IDs.

### After (FIXED - Object Format)
```json
{
  "buses": {
    "KERNEL_CORE_BUS": {
      "state": "ON",
      "workloads": [...]
    },
    "AI_BUS": {
      "state": "OFF",
      "workloads": [...]
    },
    "MENTOR_BUS": {
      "state": "OFF",
      "workloads": [...]
    }
  }
}
```

**Solution**: Bus IDs are now direct object keys, preserving capability-domain semantics.

---

## Schema Changes

1. **Top-level structure**: `buses` changed from `Array` → `Object`
2. **Bus identification**: Bus ID moved from `bus` property → **object key**
3. **State property**: Changed `status: "FROZEN"` → `state: "ON"|"OFF"`
4. **Removed redundant fields**: No longer need `bus`, `status`, `reason` at bus level

---

## Files Changed

### Core Registry Files
- `docs/WORKLOAD_FROZEN_BUS_REGISTRY.json` — Manual conversion to object format
- `frontend/public/registry/WORKLOAD_FROZEN_BUS_REGISTRY.json` — Synced corrected version

---

## Verification

After applying patch:

```bash
# 1. Check registry structure
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | keys'
# Expected: ["ADMIN_BUS", "AI_BUS", "KERNEL_CORE_BUS", "MENTOR_BUS", "PAYMENT_BUS", "PUBLIC_WEB_BUS", "SEARCH_BUS", "STAFF_BUS"]

# 2. Verify no numeric keys
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | keys | map(select(test("^[0-9]+$")))'
# Expected: []

# 3. Check bus states
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | to_entries | map({bus: .key, state: .value.state})'
# Expected: KERNEL_CORE_BUS=ON, all others=OFF

# 4. Restart frontend and visit
open http://localhost:3000/superadmin/workload-runtime
# Expected: Buses display with semantic names (AI_BUS, PAYMENT_BUS, etc.)
```

---

## Design Rationale

### Why Object Format?

1. **Semantic Clarity**: Bus IDs as keys make structure self-documenting
2. **Type Safety**: TypeScript `Record<string, BusEntry>` is more precise than `Array<{bus: string, ...}>`
3. **Performance**: O(1) lookup by bus ID instead of O(n) array search
4. **Iteration Correctness**: `Object.entries()` yields bus IDs, not array indices

### Alignment with Bus Power Policy

The registry now mirrors `kernel/policies/bus_power.py` structure:

```python
# Backend (bus_power.py)
BUS_POWER = {
  "KERNEL_CORE_BUS": "ON",
  "AI_BUS": "OFF",
  "MENTOR_BUS": "OFF",
  ...
}
```

```json
// Frontend (registry)
{
  "buses": {
    "KERNEL_CORE_BUS": { "state": "ON", ... },
    "AI_BUS": { "state": "OFF", ... },
    "MENTOR_BUS": { "state": "OFF", ... }
  }
}
```

---

## Scanner Script Note

The `scripts/build_frozen_registry.mjs` code was **already correct** — it uses:

```javascript
const buses = {};
const sortedBusNames = Array.from(busMap.keys()).sort();
sortedBusNames.forEach(busName => {
  buses[busName] = busMap.get(busName);
});
```

However, the generated file was outdated (from Phase-A.2.B array format). This patch applied **manual correction** to align registry with scanner code.

---

## Future-Proofing

To regenerate registry with correct format:

```bash
# Regenerate (when scanner is run again)
node scripts/build_frozen_registry.mjs

# Sync to frontend
./scripts/sync_registry_to_frontend.sh

# Verify
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | keys'
```

---

## Acceptance Criteria ✓

- [x] Registry uses object format with semantic bus IDs as keys
- [x] No numeric keys (`"0"`, `"1"`, etc.) in `buses` object
- [x] Each bus entry has `state: "ON"|"OFF"` and `workloads: []`
- [x] Frontend `/superadmin/workload-runtime` displays semantic bus names
- [x] No console errors or `Object.entries(undefined)` crashes
- [x] KERNEL_CORE_BUS shows `state: "ON"`, all others show `state: "OFF"`

---

**Patch Applied**: 2026-01-14  
**Schema Version**: v0.2 (object-based buses)  
**Status**: COMPLETE ✓
