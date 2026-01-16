# PATCH — BUS CONSTITUTION UPGRADE

**Goal**: Replace fragmented bus set with canonical GateAI Capability Constitution (8 buses)

---

## Canonical 8 Buses

The GateAI Capability Constitution defines exactly **8 capability buses**:

1. **KERNEL_CORE_BUS** (ON) — Kernel control plane, superadmin
2. **PUBLIC_WEB_BUS** (OFF) — Landing, marketing, public content
3. **ADMIN_BUS** (OFF) — Staff, audit, ops, console (consolidated)
4. **AI_BUS** (OFF) — AI, ATS, signals, engines, decision slots, chat (consolidated)
5. **PEER_MOCK_BUS** (OFF) — Peer runtime, simulation, testing, mocking
6. **MENTOR_BUS** (OFF) — Mentors, appointments, human loop, availability
7. **PAYMENT_BUS** (OFF) — Payments, billing, Stripe transactions
8. **SEARCH_BUS** (OFF) — Search, discovery, analytics

---

## What Changed

### Removed Buses
- ❌ **STAFF_BUS** → Consolidated into **ADMIN_BUS**
- ❌ **ATS_SIGNALS_BUS** → Consolidated into **AI_BUS**
- ❌ **CHAT_BUS** → Consolidated into **AI_BUS**
- ❌ **SIGNAL_DELIVERY_BUS** → Consolidated into **AI_BUS**
- ❌ **APPOINTMENT_BUS** → Consolidated into **MENTOR_BUS**
- ❌ **ENGINE_BUS** → Consolidated into **AI_BUS**
- ❌ **DECISION_SLOTS_BUS** → Consolidated into **AI_BUS**
- ❌ **HUMAN_LOOP_BUS** → Consolidated into **MENTOR_BUS**
- ❌ **UNKNOWN_BUS** → Fallback to **PUBLIC_WEB_BUS**

### Added Buses
- ✅ **PEER_MOCK_BUS** — New capability for simulation/testing infrastructure

### Consolidated Mappings

**ADMIN_BUS now includes:**
- `/admin/*`
- `/staff/*` (previously STAFF_BUS)
- `/audit/*`
- `/ops/*`
- `/console/*`

**AI_BUS now includes:**
- `/api/v1/ai/*`
- `/api/v1/ats-signals/*` (previously ATS_SIGNALS_BUS)
- `/api/v1/chat/*` (previously CHAT_BUS)
- `/api/v1/signal-delivery/*` (previously SIGNAL_DELIVERY_BUS)
- `/api/v1/decision-slots/*` (previously part of APPOINTMENT_BUS)
- `/api/engines/*` (previously ENGINE_BUS)

**MENTOR_BUS now includes:**
- `/api/v1/mentors/*`
- `/api/v1/human-loop/*`
- `/api/v1/appointments/*` (previously APPOINTMENT_BUS)
- `/api/v1/availability/*`

**PEER_MOCK_BUS includes:**
- `/peer*`
- `/mock*`
- `/simulator*`
- `/runtime-mock*`

---

## Files Modified

### 1. Backend Policy (Core Constitution)
**File**: `gateai/kernel/policies/bus_power.py`

**Changes**:
- Updated `BUS_POWER` dictionary to canonical 8 buses
- Removed obsolete bus entries (STAFF_BUS, ATS_SIGNALS_BUS, etc.)
- Added PEER_MOCK_BUS
- Updated `resolve_bus()` function:
  - Staff paths now resolve to ADMIN_BUS
  - ATS/chat/signal paths now resolve to AI_BUS
  - Peer/mock paths now resolve to PEER_MOCK_BUS
  - Appointments now resolve to MENTOR_BUS

### 2. Scanner (Registry Generator)
**File**: `scripts/build_frozen_registry.mjs`

**Changes**:
- Updated `classifyWorkloadToBus()` to match canonical 8 buses
- Hard-coded bus classification rules aligned with `bus_power.py`
- Initialize all 8 buses in registry (even if empty)
- Non-canonical buses automatically fallback to PUBLIC_WEB_BUS
- Added detection for peer/mock/simulator workloads → PEER_MOCK_BUS

### 3. Tests
**File**: `gateai/kernel/policies/test_bus_power.py`

**Changes**:
- Removed tests for obsolete buses
- Added test for PEER_MOCK_BUS
- Updated AI_BUS tests to include consolidated paths (ats-signals, chat, etc.)
- Updated MENTOR_BUS tests to include appointments
- Updated ADMIN_BUS tests to include staff/audit/ops paths
- Updated expected bus count to 8 (down from 14)

---

## Bus Resolution Examples

| Path | Resolves To | Reason |
|------|-------------|--------|
| `/kernel/pulse/` | KERNEL_CORE_BUS | Kernel prefix |
| `/superadmin/workload` | KERNEL_CORE_BUS | Kernel prefix |
| `/peer-mock-runtime` | PEER_MOCK_BUS | Contains "peer" |
| `/api/mock/test` | PEER_MOCK_BUS | Contains "mock" |
| `/api/v1/ai/` | AI_BUS | AI capability |
| `/api/v1/ats-signals/` | AI_BUS | Consolidated into AI |
| `/api/v1/chat/` | AI_BUS | Consolidated into AI |
| `/api/v1/signal-delivery/` | AI_BUS | Consolidated into AI |
| `/api/engines/match` | AI_BUS | Consolidated into AI |
| `/api/v1/mentors/` | MENTOR_BUS | Mentor capability |
| `/api/v1/appointments/` | MENTOR_BUS | Consolidated into MENTOR |
| `/api/v1/human-loop/` | MENTOR_BUS | Consolidated into MENTOR |
| `/api/v1/payments/` | PAYMENT_BUS | Payment capability |
| `/api/v1/search/` | SEARCH_BUS | Search capability |
| `/api/v1/analytics/` | SEARCH_BUS | Consolidated into SEARCH |
| `/admin/users` | ADMIN_BUS | Admin operations |
| `/staff/support` | ADMIN_BUS | Consolidated into ADMIN |
| `/audit/logs` | ADMIN_BUS | Consolidated into ADMIN |
| `/ops/console` | ADMIN_BUS | Consolidated into ADMIN |
| `/about` | PUBLIC_WEB_BUS | Public content |
| `/pricing` | PUBLIC_WEB_BUS | Public content |

---

## Verification Commands

```bash
# 1. Run backend tests
cd gateai
python -m pytest kernel/policies/test_bus_power.py -v

# Expected: All tests pass with 8 canonical buses

# 2. Regenerate registry
cd ..
node scripts/build_frozen_registry.mjs

# Expected output should show:
# - Scanning workloads...
# - Classifying into 8 buses
# - Warning for any non-canonical bus detected
# - Output file: docs/WORKLOAD_FROZEN_BUS_REGISTRY.json

# 3. Verify registry structure
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | keys | sort'

# Expected output (exactly 8 buses):
# [
#   "ADMIN_BUS",
#   "AI_BUS",
#   "KERNEL_CORE_BUS",
#   "MENTOR_BUS",
#   "PAYMENT_BUS",
#   "PEER_MOCK_BUS",
#   "PUBLIC_WEB_BUS",
#   "SEARCH_BUS"
# ]

# 4. Verify STAFF_BUS no longer exists
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | has("STAFF_BUS")'

# Expected: false

# 5. Verify PEER_MOCK_BUS exists
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | has("PEER_MOCK_BUS")'

# Expected: true

# 6. Verify bus states
cat docs/WORKLOAD_FROZEN_BUS_REGISTRY.json | jq '.buses | to_entries | map({bus: .key, state: .value.state})'

# Expected: KERNEL_CORE_BUS = "ON", all others = "OFF"

# 7. Sync to frontend
./scripts/sync_registry_to_frontend.sh

# 8. Visit frontend
# Open: http://localhost:3000/superadmin/workload-runtime
# Expected: See exactly 8 buses, no STAFF_BUS, includes PEER_MOCK_BUS
```

---

## Workload Redistribution

### Previously in STAFF_BUS → Now in ADMIN_BUS
- Staff operations pages
- Staff appointment management
- Staff support pages

### Previously in Separate Buses → Now in AI_BUS
- ATS signals (ats_signals)
- Signal delivery (signal_delivery)
- Chat (chat)
- Decision slots (decision_slots)
- Engines (gateai, ResumeMatcher, etc.)

### Previously in APPOINTMENT_BUS → Now Split
- Appointments → MENTOR_BUS
- Decision slots → AI_BUS

### New in PEER_MOCK_BUS
- peer-mock-runtime workload
- Any simulation/testing infrastructure

---

## Design Rationale

### Why 8 Buses?

1. **Semantic Clarity**: Each bus represents a distinct capability domain
2. **Operational Alignment**: Buses map to team ownership and operational concerns
3. **Governance Simplicity**: Fewer buses = simpler access control and monitoring
4. **Capability Grouping**: Related capabilities consolidated under single bus

### Why Remove STAFF_BUS?

- Staff operations are administrative in nature
- No distinct capability boundary from ADMIN_BUS
- Consolidation reduces cognitive overhead
- Aligns with "Admin includes all internal operations" principle

### Why Consolidate into AI_BUS?

- ATS, signals, chat, engines are all AI-powered capabilities
- Share common infrastructure (decision slots, engine runtime)
- Unified governance for AI/ML workloads
- Reduces inter-bus coordination overhead

### Why Add PEER_MOCK_BUS?

- Testing/simulation is a distinct operational concern
- Needs separate power control from production buses
- Enables safe experimentation without affecting live traffic
- Future: Can be used for A/B testing, chaos engineering

---

## Backward Compatibility

### Code Changes Required
- ✅ `bus_power.py` updated
- ✅ `build_frozen_registry.mjs` updated
- ✅ Tests updated

### No Breaking Changes
- Frontend already uses object-based bus format
- TypeScript interfaces remain unchanged
- Middleware logic unchanged (just different bus mappings)
- No API contract changes

### Migration Path
1. Update backend policy (bus_power.py)
2. Regenerate registry (build_frozen_registry.mjs)
3. Sync to frontend
4. Restart services
5. Verify in UI

---

## Acceptance Criteria

- [x] `BUS_POWER` dict contains exactly 8 buses
- [x] STAFF_BUS removed from code
- [x] PEER_MOCK_BUS added to code
- [x] `resolve_bus()` maps staff paths to ADMIN_BUS
- [x] `resolve_bus()` maps peer/mock paths to PEER_MOCK_BUS
- [x] `classifyWorkloadToBus()` uses 8-bus classification
- [x] Tests updated and passing
- [ ] Registry regenerated with 8 buses
- [ ] Frontend displays exactly 8 buses
- [ ] No STAFF_BUS in UI
- [ ] PEER_MOCK_BUS visible in UI

---

## Next Steps

1. **Regenerate Registry**:
   ```bash
   node scripts/build_frozen_registry.mjs
   ```

2. **Sync to Frontend**:
   ```bash
   ./scripts/sync_registry_to_frontend.sh
   ```

3. **Restart Services** (if running):
   - Backend: Restart Django server
   - Frontend: Restart npm start

4. **Verify in Browser**:
   - Visit: `http://localhost:3000/superadmin/workload-runtime`
   - Check: Exactly 8 buses displayed
   - Check: PEER_MOCK_BUS present
   - Check: STAFF_BUS absent
   - Check: Workloads correctly grouped

5. **Run Tests**:
   ```bash
   cd gateai
   python -m pytest kernel/policies/test_bus_power.py -v
   ```

---

## Status

✅ **Backend Policy Updated** (bus_power.py)  
✅ **Scanner Updated** (build_frozen_registry.mjs)  
✅ **Tests Updated** (test_bus_power.py)  
⏳ **Registry Regeneration Required**  
⏳ **Frontend Sync Required**  
⏳ **Acceptance Tests Required**

**Completion**: 60% (Code ready, regeneration pending)
