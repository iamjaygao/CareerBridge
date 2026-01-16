# Phase-A.1 SuperAdmin Smoke Tests

**Purpose**: Verify Kernel Pulse frontend integration in SuperAdmin world  
**Target**: `/superadmin/kernel-pulse`  
**Status**: ⏳ Awaiting Manual Verification

---

## Prerequisites

- ✅ Backend running on `http://localhost:8001`
- ✅ Frontend running on `http://localhost:3000`
- ✅ SuperAdmin user account with credentials
- ✅ Phase-A.1 backend acceptance tests passed

---

## Smoke Test Checklist

### 1. SuperAdmin Login ✅

**Steps**:
1. Navigate to `http://localhost:3000/login`
2. Enter SuperAdmin credentials
3. Click "Login"

**Expected**:
- ✅ Redirect to `/superadmin`
- ✅ URL is `http://localhost:3000/superadmin`
- ✅ Page displays: "GateAI Kernel Control Plane"
- ✅ No console errors

**Screenshot**: `smoke_test_1_login.png`

---

### 2. Navigate to Kernel Pulse ✅

**Steps**:
1. Manually navigate to `http://localhost:3000/superadmin/kernel-pulse`
2. Open Browser DevTools:
   - **Chrome/Firefox**: Press `F12` or `Cmd+Option+I` (Mac)
   - **Safari**: `Cmd+Option+I` (enable Develop menu first)
3. Click "Network" tab
4. Refresh page if needed

**Expected**:
- ✅ Page loads successfully
- ✅ URL remains `/superadmin/kernel-pulse`
- ✅ No redirect to error page
- ✅ Loading spinner appears briefly, then content displays

**Screenshot**: `smoke_test_2_page_load.png`

---

### 3. Network Request Verification ✅

**In DevTools Network Tab**:

**Required Requests** (MUST be present):
- ✅ `GET /kernel/pulse/summary/` → HTTP 200 OK
  - Request Headers: `Authorization: Bearer eyJ...`
  - Response Type: `application/json`

**Optional Requests** (Allowed):
- ✅ `GET /api/v1/users/me/` → HTTP 200 OK (auth verification)

**Forbidden Requests** (MUST NOT be present):
- ❌ NO `/api/v1/search/popular/jobs/`
- ❌ NO `/api/v1/search/popular/skills/`
- ❌ NO `/api/v1/search/popular/industries/`
- ❌ NO `/api/v1/signal-delivery/unread-count/`
- ❌ NO `/api/v1/adminpanel/system/settings/public/`
- ❌ NO `/kernel/platform-state`
- ❌ NO `/kernel/feature-flags`
- ❌ NO 404 errors
- ❌ NO polling/repeated requests (check for 5+ seconds)

**Screenshot**: `smoke_test_3_network_tab.png`

**Validation Checklist**:
```
Network Requests:
  [✓] /kernel/pulse/summary/ present
  [✓] HTTP 200 response
  [✓] No frozen module calls
  [✓] No 404 spam
  [✓] No polling detected
```

---

### 4. Console Error Check ✅

**In DevTools Console Tab**:

**Expected**:
- ✅ NO React errors
- ✅ NO API errors
- ✅ NO unhandled promise rejections
- ✅ NO 404 errors

**Allowed**:
- ✅ `[PHASE-A] Module X is frozen. Request blocked.` warnings (informational)

**Screenshot**: `smoke_test_4_console.png`

**Validation Checklist**:
```
Console:
  [✓] No red error messages
  [✓] No React warnings
  [✓] No 404 errors
  [✓] Phase-A guards working (if any)
```

---

### 5. UI Component Verification ✅

**Visual Inspection**:

**Header**:
- ✅ Title: "Kernel Pulse"
- ✅ Subtitle: "Phase-A.1 | Read-only observability plane | Pulse ABI v0.1"

**Kernel State Cards** (4 cards):
- ✅ Card 1: "Kernel Mode" - Shows badge (NORMAL/DEGRADED/LOCKED)
- ✅ Card 2: "Lock Pressure" - Shows badge (LOW/MEDIUM/HIGH)
- ✅ Card 3: "Error Rate (1h)" - Shows percentage
- ✅ Card 4: "Chaos Safe" - Shows ✅ YES or ❌ NO

**Counts Tables** (2 tables):
- ✅ Table 1: "Last 1 Hour" - Shows 5 rows (Total, Success, Retryable, Terminal, Conflict)
- ✅ Table 2: "Last 24 Hours" - Shows 5 rows (same structure)

**Active Locks Table**:
- ✅ Title: "Active Locks (N)" - Shows count
- ✅ Table headers: Type, ID, Owner, Status, Expires
- ✅ If empty: "No active locks" message

**Top Errors Table**:
- ✅ Title: "Top Errors (24h)"
- ✅ Table headers: Error Code, Count
- ✅ If empty: "No errors in last 24h" message

**Recent Syscalls Table**:
- ✅ Title: "Recent Syscalls (Last 20)"
- ✅ Table headers: Time, Syscall, Outcome, Resource, Error Code
- ✅ Scrollable (if > 10 rows)
- ✅ If empty: "No recent syscalls" message

**Screenshot**: `smoke_test_5_ui_components.png`

**Validation Checklist**:
```
UI Components:
  [✓] Header displays
  [✓] 4 kernel state cards visible
  [✓] 2 counts tables visible
  [✓] Active locks table visible
  [✓] Top errors table visible
  [✓] Recent syscalls table visible
  [✓] All text is readable
  [✓] No layout issues
```

---

### 6. Error Handling Test ⚠️

**Steps**:
1. **Stop backend server** (in backend terminal: `Ctrl+C`)
2. **Refresh frontend page**
3. **Wait 5 seconds**

**Expected**:
- ✅ Error alert displays: "Failed to load kernel pulse" or "Kernel access denied"
- ✅ NO infinite loading spinner
- ✅ NO blank white page
- ✅ NO React crash boundary

**Screenshot**: `smoke_test_6_error_handling.png`

**Recovery**:
1. **Restart backend**: `cd gateai && python3 manage.py runserver 8001`
2. **Refresh page**
3. **Verify**: Data loads successfully

---

### 7. Responsive Design Check ✅

**Steps**:
1. Resize browser window to mobile size (~375px width)
2. Verify layout adapts
3. Resize to tablet size (~768px width)
4. Resize back to desktop (~1920px width)

**Expected**:
- ✅ Cards stack vertically on mobile
- ✅ Tables remain scrollable
- ✅ No horizontal overflow
- ✅ Text remains readable at all sizes

**Screenshot**: `smoke_test_7_responsive.png`

---

### 8. Security Verification 🔒

**Test A: Non-SuperAdmin Access**

**Steps**:
1. Logout
2. Login as regular user (Student/Mentor/Staff - NOT SuperAdmin)
3. Manually navigate to `/superadmin/kernel-pulse`

**Expected**:
- ✅ Redirect to `/dashboard` or `/admin` (world-router correction)
- **OR**
- ✅ HTTP 403 error page
- ✅ NOT kernel pulse page

**Test B: Unauthenticated Access**

**Steps**:
1. Logout completely
2. Manually navigate to `/superadmin/kernel-pulse`

**Expected**:
- ✅ Redirect to `/login`
- ✅ NOT kernel pulse page

**Screenshot**: `smoke_test_8_security.png`

---

## Smoke Test Summary

### Passing Criteria

All of the following MUST pass:

- ✅ SuperAdmin can login and access `/superadmin`
- ✅ `/superadmin/kernel-pulse` page loads successfully
- ✅ Network: ONLY `/kernel/pulse/summary/` (+ optional `/me/`)
- ✅ Network: NO frozen module calls
- ✅ Network: NO 404 spam
- ✅ Console: NO errors
- ✅ UI: All 7 component sections display
- ✅ Error handling: Graceful error display when backend down
- ✅ Security: Non-SuperAdmin cannot access
- ✅ Security: Unauthenticated users redirected

---

## Quick Verification Command

Run this one-liner to check if page is accessible:

```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"SUPERUSER","password":"PASSWORD"}' | jq -r '.access')

# Test endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/ | jq '.pulse_version'

# Expected output: "0.1"
```

---

## Screenshots

Place screenshots in `docs/smoke_tests/phase_a1/`:

```
docs/smoke_tests/phase_a1/
├── smoke_test_1_login.png
├── smoke_test_2_page_load.png
├── smoke_test_3_network_tab.png
├── smoke_test_4_console.png
├── smoke_test_5_ui_components.png
├── smoke_test_6_error_handling.png
├── smoke_test_7_responsive.png
└── smoke_test_8_security.png
```

---

## Status Tracking

| Test | Status | Date | Tester | Notes |
|------|--------|------|--------|-------|
| 1. Login | ⏳ | - | - | - |
| 2. Page Load | ⏳ | - | - | - |
| 3. Network | ⏳ | - | - | - |
| 4. Console | ⏳ | - | - | - |
| 5. UI Components | ⏳ | - | - | - |
| 6. Error Handling | ⏳ | - | - | - |
| 7. Responsive | ⏳ | - | - | - |
| 8. Security | ⏳ | - | - | - |

**Legend**:
- ⏳ = Pending
- ✅ = Passed
- ❌ = Failed

---

## Sign-off

```
Tester Name: ___________________________
Date: ___________________________
Signature: ___________________________

Result: [ ] PASSED  [ ] FAILED

Notes:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**Phase-A.1 SuperAdmin Smoke Tests**  
**Status**: ⏳ Awaiting Manual Verification  
**Date**: 2026-01-14
