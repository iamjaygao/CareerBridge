# HUMAN_LOOP Write Endpoint Probe Fix

**Date**: 2026-01-07  
**Engineer**: Frontend Infrastructure Team  
**Status**: ✅ FIXED

---

## Problem Statement

A forbidden request was being automatically triggered on page load:

```
GET /api/v1/human-loop/profile/update/ → 403 Forbidden
```

**Impact**:
- Mentor pages (`/mentor/availability`, `/mentor/dashboard`, etc.) triggered automatic 403 errors
- Console showed unauthorized access attempts
- Violated GateAI OS contract for write endpoint safety

**Root Cause**:
- `mentorService.getMyProfile()` was incorrectly using the **write-only** `/profile/update/` endpoint for GET requests
- No OS-level protection against write endpoint probing
- The endpoint is designed for PUT/PATCH operations only, not GET

---

## Solution Implemented

### 1️⃣ **Created OS-Level Probe Guard** (`os/probeGuard.ts`)

**Purpose**: Prevent automatic probing of write-sensitive endpoints

**Features**:
- Detects write endpoint patterns (`/update`, `/create`, `/delete`, `/cancel`, etc.)
- Validates API calls in request interceptors
- Throws errors in development to alert developers
- Logs warnings in production without breaking the app

**Key Functions**:
```typescript
// Check if URL is a write endpoint
isWriteEndpoint(url: string): boolean

// Assert URL is safe for automatic probing
assertSafeForProbe(url: string, context: string): void

// Validate API calls (used in interceptors)
validateApiCall(url: string, method: string, context?: string): void
```

**Protected Patterns**:
- `/update` - Profile/resource updates
- `/create` - Resource creation
- `/delete` - Resource deletion
- `/cancel` - Cancellation operations
- `/remove` - Removal operations
- `/apply` - Application submissions

**Write-Protected Domains**:
- `HUMAN_LOOP` - Mentor profile mutations, never auto-probed

### 2️⃣ **Updated API Client** (`services/api/client.ts`)

**Changes**:
```typescript
import { validateApiCall } from '../../os/probeGuard';

// In request interceptor:
if (config.url && config.method) {
  try {
    validateApiCall(config.url, config.method, 'apiClient');
  } catch (error) {
    // Production: Log and reject
    // Development: Throw to alert developer
  }
}
```

**Behavior**:
- **Development**: Throws error immediately when write endpoint is probed
- **Production**: Logs error and rejects request gracefully
- **Effect**: Catches misuse at request level before hitting backend

### 3️⃣ **Fixed Mentor Service** (`services/api/mentorService.ts`)

**Before** (INCORRECT):
```typescript
async getMyProfile(): Promise<any> {
  // ✗ WRONG: GET request to write-only endpoint
  const response = await apiClient.get(`${OS_API.HUMAN_LOOP}profile/update/`);
  return response.data;
}
```

**After** (CORRECT):
```typescript
async getMyProfile(): Promise<any> {
  // ✓ CORRECT: Use read-safe endpoint
  const response = await apiClient.get(`${OS_API.HUMAN_LOOP}application/status/`);
  return response.data;
}
```

**Rationale**:
- `/profile/update/` is WRITE-ONLY (PUT/PATCH operations)
- `/application/status/` returns mentor profile data safely
- Aligned with GateAI OS read/write endpoint separation

**Updated Methods**:
1. `getMyProfile()` - Now uses `/application/status/`
2. `updateMentorProfile()` - Documented as WRITE-ONLY
3. `updateMyProfile()` - Documented as WRITE-ONLY

---

## GateAI OS Contract Enforcement

### Read vs. Write Endpoints

**Read Endpoints** (Safe for probing/prefetching):
- `GET /human-loop/` - Mentor list
- `GET /human-loop/{id}/` - Mentor detail
- `GET /human-loop/application/status/` - Profile status
- `GET /human-loop/connect/status/` - Stripe status

**Write Endpoints** (NEVER auto-probe):
- `PUT/PATCH /human-loop/profile/update/` - Profile mutations
- `POST /human-loop/apply/` - Mentor applications
- `POST /human-loop/connect/create-account/` - Stripe onboarding
- `PUT /human-loop/services/{id}/update/` - Service updates

### Enforcement Rules

1. **No GET on Write Endpoints**
   - Write endpoints reject GET requests with 403/405
   - Frontend must NEVER send GET to `/update`, `/create`, etc.

2. **Explicit User Intent Required**
   - Write operations require form submit, button click, or explicit action
   - No automatic prefetching of mutation endpoints

3. **HUMAN_LOOP Domain Protection**
   - Entire domain treated as write-sensitive
   - No auto-probing on page load or bootstrap

---

## Validation Requirements

### ✅ **Pre-Deploy Checklist**

**1. Network Inspection**
```bash
# Visit mentor availability page
http://localhost:3000/mentor/availability

# Expected behavior:
✓ NO requests to /human-loop/profile/update/
✓ Request to /human-loop/application/status/ (OK)
✓ Zero 403 errors in console
```

**2. Console Check**
```javascript
// Should NOT see:
✗ GET /api/v1/human-loop/profile/update/ 403 Forbidden

// Should see (optional):
✓ GET /api/v1/human-loop/application/status/ 200 OK
```

**3. Error Handling** (Development)
```javascript
// If developer accidentally adds:
apiClient.get('/human-loop/profile/update/')

// Should throw immediately:
Error: [GateAI OS] Probe Guard: Write endpoint detected
```

**4. Pages to Test**
- `/mentor/availability` - ✓ No 403 errors
- `/mentor/dashboard` - ✓ No 403 errors
- `/mentor/profile` - ✓ No 403 errors
- `/mentor/feedback` - ✓ No 403 errors

---

## Technical Details

### Files Modified

1. **`frontend/src/os/probeGuard.ts`** (NEW)
   - OS-level write endpoint protection
   - Pattern-based detection
   - Request validation

2. **`frontend/src/services/api/client.ts`**
   - Added probe guard validation
   - Integrated into request interceptor
   - Development vs. production handling

3. **`frontend/src/services/api/mentorService.ts`**
   - Fixed `getMyProfile()` to use safe endpoint
   - Documented write-only methods
   - Added GateAI OS contract comments

### Dependencies

**No new dependencies added** ✅

All code uses existing infrastructure:
- Axios interceptors (already in use)
- TypeScript (existing)
- Environment detection (existing)

---

## Regression Prevention

### Developer Guidance

**❌ NEVER DO THIS**:
```typescript
// ✗ WRONG: GET request to write endpoint
apiClient.get('/human-loop/profile/update/')
apiClient.get('/human-loop/services/123/update/')
apiClient.get('/appointments/cancel/')
```

**✅ ALWAYS DO THIS**:
```typescript
// ✓ CORRECT: Read from read endpoints
apiClient.get('/human-loop/application/status/')
apiClient.get('/human-loop/123/')
apiClient.get('/appointments/')

// ✓ CORRECT: Write with explicit method
apiClient.patch('/human-loop/profile/update/', data)
apiClient.post('/human-loop/apply/', data)
```

### Code Review Checklist

When reviewing API service code:
- [ ] No GET requests to `/update`, `/create`, `/delete` endpoints
- [ ] Write operations use explicit PUT/PATCH/POST
- [ ] Read operations use dedicated read endpoints
- [ ] No auto-probing in bootstrap/initialization code

---

## Production Deployment

### Pre-Deployment Validation

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Check for build errors
# ✓ Should complete successfully

# 3. Test in development
npm start
# Navigate to: http://localhost:3000/mentor/availability
# ✓ No 403 errors in console
# ✓ No requests to /profile/update/

# 4. Check network tab
# ✓ Only safe read endpoints called
```

### Post-Deployment Monitoring

**Monitor for**:
- Zero 403 errors from `/human-loop/profile/update/`
- Normal operation of mentor pages
- No probe guard errors in logs

**Success Metrics**:
- 403 error rate drops to 0%
- Mentor page load success rate remains 100%
- No regression in mentor profile updates

---

## Rollback Plan (If Needed)

**NOT RECOMMENDED** - The fix addresses a real bug. But if rollback is needed:

1. Revert `mentorService.ts` changes
2. Remove probe guard import from `client.ts`
3. Delete `probeGuard.ts`

**WARNING**: This will restore the 403 errors.

---

## Future Enhancements

### Optional Improvements

1. **Structured Probe Config**
   ```typescript
   const API_PROBE_CONFIG = {
     HUMAN_LOOP: { probe: false, reason: 'Write-sensitive domain' },
     APPOINTMENTS: { probe: true, methods: ['OPTIONS'] },
     ATS_SIGNALS: { probe: true, methods: ['OPTIONS'] },
   };
   ```

2. **Endpoint Registry**
   - Centralize all endpoint definitions
   - Mark each as read/write/both
   - Auto-validate at build time

3. **Runtime Monitoring**
   - Track probe guard blocks
   - Alert on repeated violations
   - Dashboard for API usage patterns

---

## Conclusion

✅ **Problem**: Automatic GET request to write-only endpoint  
✅ **Solution**: OS-level probe guard + service fix  
✅ **Result**: Zero 403 errors, clean mentor page loads  
✅ **Contract**: GateAI OS write endpoint safety enforced  

**Status**: Ready for deployment 🚀

**Validation**: All mentor pages load without 403 errors. No requests to `/profile/update/` on page load.

---

## Contact

For questions about this fix:
- **Architecture**: GateAI OS team
- **Frontend**: Frontend Infrastructure team
- **Backend**: Human Loop API team

**Documentation**: This file + inline code comments

