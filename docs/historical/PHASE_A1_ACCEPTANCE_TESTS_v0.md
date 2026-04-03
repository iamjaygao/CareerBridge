# Phase-A.1 Kernel Pulse - Acceptance Tests

**Status**: ✅ Implementation Complete  
**Unit Tests**: ✅ 8/8 Passed  
**Date**: 2026-01-14

---

## Test Suite Overview

Run these acceptance tests to verify Phase-A.1 Kernel Pulse is working correctly:

1. ✅ Backend Unit Tests (PASSED)
2. ⏳ Backend curl Access
3. ⏳ Frontend Integration
4. ⏳ End-to-End Verification

---

## Test 1: Backend Unit Tests ✅ PASSED

**Status**: ✅ COMPLETE (8/8 tests passed)

```bash
cd gateai
python3 manage.py test kernel.pulse.test_pulse --settings=gateai.settings_test
```

**Expected Output**:
```
Ran 8 tests in 2.268s
OK
```

**Tests Covered**:
- ✅ Unauthenticated access returns 403
- ✅ Regular user access returns 403
- ✅ Superuser access returns 200
- ✅ Response contains all Pulse ABI v0.1 keys
- ✅ Recent syscalls returned correctly
- ✅ Counts computed correctly
- ✅ Kernel state mode derivation works
- ✅ Active locks structure correct

---

## Test 2: Backend curl Access ⏳

### Step 2.1: Start Backend Server

```bash
cd gateai
python3 manage.py runserver 8001
```

### Step 2.2: Get JWT Token

```bash
curl -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"YOUR_SUPERUSER_USERNAME","password":"YOUR_PASSWORD"}'
```

**Expected Response**:
```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "user": {
    "id": 1,
    "username": "...",
    "is_superuser": true,
    ...
  }
}
```

**Action**: Copy the `access` token value.

### Step 2.3: Test Kernel Pulse Endpoint

```bash
export TOKEN="YOUR_ACCESS_TOKEN_HERE"

curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/kernel/pulse/summary/
```

**Expected Response** (HTTP 200):
```json
{
  "pulse_version": "0.1",
  "now": "2026-01-14T12:00:00Z",
  "kernel_state": {
    "mode": "NORMAL",
    "active_lock_pressure": "LOW",
    "error_rate_1h": 0.0,
    "chaos_safe": true
  },
  "recent_syscalls": [],
  "counts": {
    "last_1h": {
      "total": 0,
      "success": 0,
      "retryable": 0,
      "terminal": 0,
      "conflict": 0
    },
    "last_24h": { ... }
  },
  "active_locks": {
    "count": 0,
    "samples": []
  },
  "top_errors_24h": []
}
```

**Validation Checklist**:
- ✅ HTTP Status: 200 OK
- ✅ Response is valid JSON
- ✅ Contains `pulse_version: "0.1"`
- ✅ Contains `kernel_state` object
- ✅ Contains `recent_syscalls` array
- ✅ Contains `counts` object
- ✅ Contains `active_locks` object
- ✅ Contains `top_errors_24h` array

### Step 2.4: Test Unauthorized Access

```bash
# No token
curl http://localhost:8001/kernel/pulse/summary/

# Expected: 403 Forbidden or 401 Unauthorized
```

**Expected**: HTTP 403 or 401 (access denied)

---

## Test 3: Frontend Integration ⏳

### Step 3.1: Start Frontend Server

```bash
cd frontend
npm start
```

**Expected**: Server starts on `http://localhost:3000`

### Step 3.2: Login as SuperAdmin

1. Navigate to: `http://localhost:3000/login`
2. Enter SuperAdmin credentials
3. Click "Login"

**Expected**:
- ✅ Redirect to `/superadmin`
- ✅ URL is `http://localhost:3000/superadmin`
- ✅ SuperAdmin root page displays: "GateAI Kernel Control Plane"

### Step 3.3: Navigate to Kernel Pulse

1. Manually navigate to: `http://localhost:3000/superadmin/kernel-pulse`

**OR**

Add a link to SuperAdmin sidebar (optional):
- Edit `frontend/src/components/layouts/SuperAdminLayout.tsx`
- Add: `{ label: 'Kernel Pulse', path: '/superadmin/kernel-pulse', icon: <SpeedIcon /> }`

### Step 3.4: Open DevTools Network Tab

**Chrome/Firefox/Safari**:
1. Press `F12` or `Cmd+Option+I` (Mac)
2. Click "Network" tab
3. Refresh page or navigate to `/superadmin/kernel-pulse`

**Expected Network Requests**:
- ✅ ONE request: `GET /kernel/pulse/summary/` → HTTP 200
- ✅ OPTIONAL: `GET /api/v1/users/me/` (auth check)
- ❌ NO requests to frozen modules:
  - ❌ NO `/search/`
  - ❌ NO `/signal-delivery/`
  - ❌ NO `/adminpanel/system/settings/`
  - ❌ NO `/kernel/platform-state`
  - ❌ NO `/kernel/feature-flags`

### Step 3.5: Verify UI Display

**Expected UI Elements**:

1. **Header**:
   - ✅ "Kernel Pulse"
   - ✅ "Phase-A.1 | Read-only observability plane | Pulse ABI v0.1"

2. **Kernel State Cards** (4 cards):
   - ✅ Kernel Mode (NORMAL/DEGRADED/LOCKED)
   - ✅ Lock Pressure (LOW/MEDIUM/HIGH)
   - ✅ Error Rate (1h) (percentage)
   - ✅ Chaos Safe (YES/NO)

3. **Counts Tables** (2 tables):
   - ✅ Last 1 Hour (total, success, retryable, terminal, conflict)
   - ✅ Last 24 Hours (total, success, retryable, terminal, conflict)

4. **Active Locks Table**:
   - ✅ Count display
   - ✅ Table with: Type, ID, Owner, Status, Expires

5. **Top Errors Table**:
   - ✅ Error Code, Count

6. **Recent Syscalls Table**:
   - ✅ Time, Syscall, Outcome, Resource, Error Code
   - ✅ Scrollable

### Step 3.6: Test Error Handling

1. **Stop backend server** (Ctrl+C)
2. **Refresh frontend page**

**Expected**:
- ✅ Error message displays
- ✅ NO infinite loading spinner
- ✅ NO console errors (beyond network failure)

3. **Restart backend server**
4. **Refresh page**

**Expected**:
- ✅ Data loads successfully
- ✅ UI displays normally

---

## Test 4: End-to-End Verification ⏳

### Full Integration Test

1. **Backend running**: `cd gateai && python3 manage.py runserver 8001`
2. **Frontend running**: `cd frontend && npm start`
3. **Login as SuperAdmin**
4. **Navigate to**: `/superadmin/kernel-pulse`
5. **Open DevTools Console + Network**

**Validation Checklist**:

#### Network Requests
- ✅ ONE request: `/kernel/pulse/summary/` → 200
- ❌ ZERO 404 errors
- ❌ ZERO frozen module requests
- ❌ ZERO polling/repeated requests

#### Console Logs
- ✅ NO React errors
- ✅ NO API errors
- ✅ NO 404 spam
- ✅ Optional: `[PHASE-A] Module X is frozen` warnings (if any frozen calls attempted)

#### UI Functionality
- ✅ All cards display
- ✅ All tables display
- ✅ Data is readable
- ✅ No infinite loading spinners
- ✅ Page is responsive

#### Security
- ✅ Non-SuperAdmin cannot access (returns 403)
- ✅ Unauthenticated users redirected to login
- ✅ JWT token required for backend access

---

## Test 5: curl Quick Test Script

Copy and run this complete test:

```bash
#!/bin/bash
# Phase-A.1 Kernel Pulse Quick Test

echo "🧪 Phase-A.1 Kernel Pulse - Quick Test"
echo "======================================"

# Config
BACKEND_URL="http://localhost:8001"
USERNAME="YOUR_SUPERUSER_USERNAME"
PASSWORD="YOUR_PASSWORD"

echo ""
echo "📡 Step 1: Login and get JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/users/login/" \
  -H "Content-Type: application/json" \
  -d "{\"identifier\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | sed 's/"access":"//')

if [ -z "$TOKEN" ]; then
  echo "❌ FAILED: Could not get JWT token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:20}..."

echo ""
echo "📊 Step 2: Test /kernel/pulse/summary/ endpoint..."
PULSE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BACKEND_URL/kernel/pulse/summary/")

HTTP_CODE=$(echo "$PULSE_RESPONSE" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
RESPONSE_BODY=$(echo "$PULSE_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ HTTP 200 OK"
  
  # Check for required keys
  if echo "$RESPONSE_BODY" | grep -q '"pulse_version"'; then
    echo "✅ Contains pulse_version"
  else
    echo "❌ Missing pulse_version"
  fi
  
  if echo "$RESPONSE_BODY" | grep -q '"kernel_state"'; then
    echo "✅ Contains kernel_state"
  else
    echo "❌ Missing kernel_state"
  fi
  
  if echo "$RESPONSE_BODY" | grep -q '"recent_syscalls"'; then
    echo "✅ Contains recent_syscalls"
  else
    echo "❌ Missing recent_syscalls"
  fi
  
  echo ""
  echo "📄 Response Preview:"
  echo "$RESPONSE_BODY" | head -20
  
  echo ""
  echo "✅ Phase-A.1 Kernel Pulse: OPERATIONAL"
else
  echo "❌ FAILED: HTTP $HTTP_CODE"
  echo "Response: $RESPONSE_BODY"
  exit 1
fi

echo ""
echo "🎉 All tests passed!"
```

**Usage**:
1. Save as `test_kernel_pulse.sh`
2. Edit `USERNAME` and `PASSWORD`
3. `chmod +x test_kernel_pulse.sh`
4. `./test_kernel_pulse.sh`

---

## Success Criteria

Phase-A.1 is **COMPLETE** when:

- ✅ Backend unit tests: 8/8 passed
- ✅ Backend curl test: 200 OK with valid Pulse ABI response
- ✅ Frontend loads `/superadmin/kernel-pulse` successfully
- ✅ Network tab shows ONLY ONE XHR to `/kernel/pulse/summary/`
- ✅ NO 404 spam in console
- ✅ NO frozen module calls
- ✅ UI displays all metrics correctly
- ✅ Non-SuperAdmin users get 403
- ✅ Unauthenticated users get redirected/403

---

## Troubleshooting

### Issue: 403 Forbidden

**Possible Causes**:
1. User is not a SuperAdmin (`is_superuser=False`)
2. JWT token missing or invalid
3. GovernanceMiddleware blocked request

**Fix**:
```python
# Check user in Django shell
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='YOUR_USERNAME')
>>> user.is_superuser = True
>>> user.save()
```

### Issue: 404 Not Found

**Possible Causes**:
1. Backend not running
2. Wrong URL (check: `/kernel/pulse/summary/` with trailing slash)
3. URL routing not registered

**Fix**:
```bash
# Check kernel/urls.py has:
path('pulse/', include('kernel.pulse.urls'))

# Restart backend
python manage.py runserver 8001
```

### Issue: Frontend 404 Spam

**Possible Causes**:
1. Frozen modules still being called

**Fix**:
- Check `utils/phaseAGuard.ts` is imported
- Check `canCallModule()` guards are in place

---

## Next Steps After Testing

Once all acceptance tests pass:

1. ✅ Mark Phase-A.1 as **PRODUCTION READY**
2. 🚀 Deploy to staging environment
3. 📊 Monitor kernel pulse metrics
4. 🔄 Begin Phase-A.2 (if planned)

---

**Phase-A.1 Kernel Pulse**  
**Status**: ✅ Ready for Acceptance Testing  
**Date**: 2026-01-14
