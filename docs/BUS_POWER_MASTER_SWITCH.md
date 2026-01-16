# Bus Power Master Switch — Phase-A Installation

**Date**: 2026-01-14  
**Status**: ✅ INSTALLED (全 OFF 模式)  
**Purpose**: 能力总线总闸基础设施

---

## Executive Summary

Phase-A "Bus Power Master Switch"（能力总线总闸）已成功安装。这是一个中间件级别的统一开关机制，可以在不修改业务代码的情况下，快速禁用/启用整个功能模块。

**Phase-A 状态**: 所有总线 OFF（除 KERNEL_CORE_BUS），仅用于拦截与准备，不放电。

---

## What Is Bus Power?

**Bus Power** 是一种**基础设施级别的能力控制机制**，类似于电力系统的总闸：

- **ON**: 总线通电，请求可以通过（进入正常治理流程）
- **OFF**: 总线断电，请求立即返回 404（不进入业务逻辑）

### Key Benefits

1. **统一控制**: 一个开关控制整个能力域
2. **零业务侵入**: 不修改任何业务代码
3. **快速响应**: 中间件层面拦截，性能开销极小
4. **准备未来**: 为 Phase-B 能力激活做准备

---

## Architecture

### Bus Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     HTTP Request                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│              Bus Power Master Switch (Middleware)                │
│                                                                   │
│  resolve_bus(path) → bus_id                                      │
│  is_bus_powered(bus_id) → True/False                             │
│                                                                   │
│  if False → return 404                                           │
│  if True  → continue to governance                               │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Normal Governance Pipeline                     │
│         (World Resolution → Feature Flags → Routing)             │
└─────────────────────────────────────────────────────────────────┘
```

### Bus Definitions (Phase-A)

| Bus ID | Paths | State | Purpose |
|--------|-------|-------|---------|
| `KERNEL_CORE_BUS` | `/kernel/*`, `/superadmin/*` | **ON** | Kernel control plane |
| `AI_BUS` | `/api/v1/ai/*`, `/api/engines/ai/*` | OFF | AI capabilities |
| `MENTOR_BUS` | `/api/v1/mentors/*`, `/api/v1/human-loop/*` | OFF | Mentor/human loop |
| `PAYMENT_BUS` | `/api/v1/payments/*` | OFF | Payment/transactions |
| `SEARCH_BUS` | `/api/v1/search/*` | OFF | Search/discovery |
| `ATS_SIGNALS_BUS` | `/api/v1/ats-signals/*` | OFF | ATS signals |
| `CHAT_BUS` | `/api/v1/chat/*` | OFF | Chat/communication |
| `SIGNAL_DELIVERY_BUS` | `/api/v1/signal-delivery/*` | OFF | Signal delivery |
| `APPOINTMENT_BUS` | `/api/v1/appointments/*`, `/api/v1/decision-slots/*` | OFF | Appointments |
| `ENGINE_BUS` | `/api/engines/*` | OFF | External engines |
| `ADMIN_BUS` | `/admin/*` | OFF | Admin operations |
| `STAFF_BUS` | `/staff/*` | OFF | Staff operations |
| `PUBLIC_WEB_BUS` | `/`, `/about`, `/login`, etc. | OFF | Public web |

---

## Implementation

### 1. Bus Power Policy

**File**: `gateai/kernel/policies/bus_power.py`

```python
BUS_POWER = {
    "KERNEL_CORE_BUS": "ON",   # Only kernel is ON
    "AI_BUS": "OFF",
    "MENTOR_BUS": "OFF",
    # ... all other buses OFF
}
```

**Key Functions**:
- `resolve_bus(path)`: Map HTTP path to bus ID
- `is_bus_powered(bus)`: Check if bus is ON
- `get_bus_state(bus)`: Get bus state ("ON"/"OFF")

### 2. Middleware Integration

**File**: `gateai/kernel/governance/middleware.py`

**Added to `__call__` (Step 0)**:
```python
# STEP 0: Bus Power Master Switch Check
bus = resolve_bus(request.path)
request.bus = bus  # Attach for observability

if not is_bus_powered(bus):
    # Bus is OFF - return 404 immediately
    logger.info('Bus power OFF - blocking request', ...)
    return HttpResponse(status=404)

# Bus is ON - continue to normal governance
```

**Execution Order**:
1. **Step 0**: Bus Power Check (NEW)
2. Step 1: JWT Authentication (kernel only)
3. Step 2: World Resolution
4. Step 3: Kernel Sovereign Guard
5. Step 4: Userland Governance

---

## Verification

### Run Verification Script

```bash
# Start backend server
cd gateai && python manage.py runserver

# In another terminal, run verification
./scripts/verify_bus_power.sh
```

### Expected Results

```
Test 1: KERNEL_CORE_BUS (Should be ON → 200)
  ✅ PASS (got 200)

Test 2: AI_BUS (Should be OFF → 404)
  ✅ PASS (got 404)

Test 3: MENTOR_BUS (Should be OFF → 404)
  ✅ PASS (got 404)

... (all other buses)

✅ All tests passed!
Bus Power Master Switch is correctly installed.
```

### Manual curl Commands

```bash
# Test KERNEL_CORE_BUS (ON)
export TOKEN="your_jwt_token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/kernel/pulse/summary/
# Expected: 200 OK

# Test AI_BUS (OFF)
curl http://localhost:8000/api/v1/ai/
# Expected: 404

# Test MENTOR_BUS (OFF)
curl http://localhost:8000/api/v1/mentors/
# Expected: 404

# Test PAYMENT_BUS (OFF)
curl http://localhost:8000/api/v1/payments/
# Expected: 404

# Test SEARCH_BUS (OFF)
curl http://localhost:8000/api/v1/search/
# Expected: 404

# Test ADMIN_BUS (OFF)
curl http://localhost:8000/admin/
# Expected: 404
```

---

## Unit Tests

**File**: `gateai/kernel/policies/test_bus_power.py`

**Run Tests**:
```bash
cd gateai
pytest kernel/policies/test_bus_power.py -v
```

**Test Coverage**:
- ✅ Bus resolution logic (13 tests)
- ✅ Bus power state logic (4 tests)
- ✅ Phase-A constraints (3 tests)

**Total**: 20 tests, all passing

---

## Files Changed

### New Files (4)
1. `gateai/kernel/policies/__init__.py` — Policy package init
2. `gateai/kernel/policies/bus_power.py` — Bus power policy
3. `gateai/kernel/policies/test_bus_power.py` — Unit tests
4. `scripts/verify_bus_power.sh` — Verification script
5. `docs/BUS_POWER_MASTER_SWITCH.md` — This documentation

### Modified Files (1)
1. `gateai/kernel/governance/middleware.py` — Added bus power check

---

## Constraints Compliance

### Phase-A Hard Constraints ✅
- ✅ **No business logic changes**
- ✅ **No write interface** (policy is read-only)
- ✅ **Default all OFF** (except KERNEL_CORE_BUS)
- ✅ **Kernel continues ON** (no disruption)

### Zero-Noise Design ✅
- ✅ **Minimal middleware overhead** (one function call per request)
- ✅ **Early exit** (404 before any business logic)
- ✅ **Observable** (logs bus state for debugging)

---

## Why This Design?

### Problem: Ad-Hoc Capability Control

Before Bus Power:
- Feature flags mixed with business logic
- Hard to disable entire capability domains
- Each module needs individual configuration
- No centralized "emergency stop"

### Solution: Centralized Bus Control

After Bus Power:
- One switch per capability domain
- Middleware-level control (before business logic)
- No code changes needed to disable/enable
- Emergency stop capability for operations

### Phase-A Strategy

**Install but don't use**: Phase-A 只是安装基础设施，不激活任何能力。所有总线 OFF（除 KERNEL），为 Phase-B 的能力激活做准备。

---

## Future: Phase-B Activation

When ready to activate a capability:

1. **Update Policy**:
   ```python
   BUS_POWER = {
       "KERNEL_CORE_BUS": "ON",
       "AI_BUS": "ON",  # ← Turn ON when ready
       # ...
   }
   ```

2. **Deploy**:
   - No code changes needed
   - Just update policy file
   - Restart server (or hot-reload if supported)

3. **Verify**:
   ```bash
   curl http://localhost:8000/api/v1/ai/
   # Now: 200 OK (instead of 404)
   ```

---

## Observability

### Request Attributes

Each request now has:
- `request.bus`: Bus ID (e.g., "KERNEL_CORE_BUS", "AI_BUS")
- `request.world`: World ID (e.g., "kernel", "app")

### Logs

```python
logger.info('Bus power OFF - blocking request', extra={
    'path': request.path,
    'bus': bus,
    'state': get_bus_state(bus)
})
```

### Monitoring

Can track:
- Requests blocked per bus
- Bus activation status
- Emergency stop usage

---

## Emergency Operations

### Emergency Stop All (Future)

```python
# In emergency, can quickly disable all buses
BUS_POWER = {k: "OFF" for k in BUS_POWER.keys()}
BUS_POWER["KERNEL_CORE_BUS"] = "ON"  # Keep kernel
```

### Selective Activation (Future)

```python
# Only enable specific buses
BUS_POWER = {
    "KERNEL_CORE_BUS": "ON",
    "SEARCH_BUS": "ON",  # Only search
    # All others remain OFF
}
```

---

## FAQ

### Q: Why not use feature flags?

**A**: Feature flags operate at **business logic** level. Bus Power operates at **infrastructure** level (middleware). Bus Power is for **capability domains**, not individual features.

### Q: What happens to existing feature flags?

**A**: Feature flags still work! Bus Power runs **before** feature flags:
1. Bus Power check (domain-level)
2. If bus ON → proceed to feature flags (feature-level)
3. If bus OFF → return 404 (no feature flag check)

### Q: Can I turn buses ON/OFF at runtime?

**A**: Phase-A uses static policy (requires restart). Phase-B may add dynamic control via admin UI.

### Q: Why is UNKNOWN bus powered (fail-open)?

**A**: For backward compatibility. Unknown paths are not governed by bus power, allowing new features without immediate policy update.

---

## Status

**Installation**: ✅ COMPLETE  
**Testing**: ✅ PASSED (20 unit tests + verification script)  
**Phase-A State**: 全 OFF（除 KERNEL）  
**Ready for**: Phase-B capability activation

---

**Delivered**: 2026-01-14  
**Phase**: A — Bus Power Installation  
**Next**: Phase-B — Selective Activation
