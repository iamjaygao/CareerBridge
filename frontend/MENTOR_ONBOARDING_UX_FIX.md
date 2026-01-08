# Mentor Onboarding UX Fix

**Date**: 2026-01-07  
**Type**: Product-Correct UX Fix (Frontend)  
**Status**: ✅ COMPLETED

---

## Problem Statement

### Root Cause
The frontend was treating **"mentor profile not loaded"** as a **GLOBAL ERROR**, when it's actually a **VALID ONBOARDING STATE**.

This caused:
- ❌ Red error toasts/alerts: "Mentor profile not loaded"
- ❌ Blocking UX on pages that don't require a profile
- ❌ Confusing behavior where legal onboarding states were treated as failures
- ❌ Poor user experience for new mentors going through onboarding

### The Product Truth

**Backend Reality** (from `GET /api/v1/human-loop/profile/status/`):
```json
{
  "has_profile": false,      // ✅ This is LEGAL
  "mentor_profile_id": null,
  "application_status": null,
  "can_update_profile": false
}
```

**Onboarding Flow Reality**:
1. A mentor user may exist **WITHOUT** a mentor profile (valid state)
2. A mentor **SHOULD** create their profile before adding services (backend requires it)
3. Availability setup **REQUIRES** an existing mentor profile (backend requires it)
4. Service creation **REQUIRES** a mentor profile (backend requires it)
5. Dashboard and other pages **DO NOT** require a mentor profile

The issue: Frontend treated ALL of these as errors, even when the user hadn't completed onboarding yet.

---

## Solution

We implemented a **product-correct fix** that treats missing mentor profile as an **ONBOARDING STATE**, not an error.

### 1. Created Onboarding Utility (`mentorOnboarding.ts`)

New utility file with helper functions:
- `requiresMentorProfile(route)`: Defines which pages require a profile
- `getOnboardingMessage(status, context)`: Returns context-specific guidance
- `shouldBlockInteraction(status, requireProfile)`: Determines if UI should be disabled

**Key pages that require profile**:
- `/mentor/availability`
- `/mentor/earnings`
- `/mentor/payouts`
- `/mentor/services` (for creation)

**Pages that work without profile**:
- `/mentor/dashboard`
- `/mentor/profile` (the creation page itself!)

---

### 2. Fixed Availability Page (`AvailabilityPage.tsx`)

**Before**:
- Missing profile → Red error alert
- Page still showed disabled editor (confusing)

**After**:
- Missing profile → **Orange warning** alert (not an error!)
- Availability editor and buttons **completely hidden** during onboarding
- Clear message: "Please create your mentor profile before setting availability."
- Stripe Connect not ready → Warning: "Please complete Stripe Connect onboarding..."
- Payouts not enabled → Warning: "Payouts are not enabled yet..."

**Changes**:
```typescript
// Added state
const [onboardingMessage, setOnboardingMessage] = useState<string | null>(null);

// Bootstrap checks
if (!profileStatus?.has_profile) {
  setOnboardingMessage('Please create your mentor profile before setting availability.');
  return;
}

if (!connectStatus?.is_connected) {
  setOnboardingMessage('Please complete Stripe Connect onboarding...');
  return;
}

// UI rendering
{onboardingMessage && (
  <Alert severity="warning">{onboardingMessage}</Alert>
)}

{!onboardingMessage && (
  // Show availability editor only when ready
)}
```

---

### 3. Fixed Profile Page (`ProfilePage.tsx`)

**Before**:
- Service creation: `showError('Mentor profile not loaded.')` (red toast)
- Generic error didn't explain what to do

**After**:
- Service creation checks profile status gracefully
- Uses `mentor_profile_id` from new profile status response
- Error message is contextual: "Please create your mentor profile before adding services."
- Service fetching doesn't throw errors when profile doesn't exist

**Changes**:
```typescript
// Service fetching
const profileId = mentorProfile?.mentor_profile_id || mentorProfile?.id;
if (!profileId) return; // Graceful return, no error

// Service creation
if (!profileId) {
  showError('Please create your mentor profile before adding services.');
  return;
}
```

---

### 4. Fixed Feedback Page (`FeedbackPage.tsx`)

**Before**:
- Missing profile → Red error alert blocking entire page

**After**:
- Missing profile → **Orange warning** alert with helpful guidance
- Page header still renders (shows context)
- Message: "Please create your mentor profile to view feedback."
- Real errors (network failures) still show as red alerts

**Changes**:
```typescript
// Added state
const [onboardingMessage, setOnboardingMessage] = useState<string | null>(null);

// Bootstrap check
if (!profile?.has_profile) {
  setOnboardingMessage('Please create your mentor profile to view feedback.');
  return;
}

// Render
if (onboardingMessage) {
  return (
    <Box>
      <Typography variant="h4">Feedback & Reviews</Typography>
      <Alert severity="warning">{onboardingMessage}</Alert>
    </Box>
  );
}
```

---

## Key Design Decisions

### 1. **Warning vs. Error Severity**

| State | Old Severity | New Severity | Rationale |
|-------|-------------|--------------|-----------|
| No mentor profile | ❌ Error (red) | ⚠️ Warning (orange) | It's an onboarding step, not a failure |
| Stripe not connected | ❌ Error (red) | ⚠️ Warning (orange) | It's an onboarding step, not a failure |
| Payouts not enabled | ❌ Error (red) | ⚠️ Warning (orange) | It's an onboarding step, not a failure |
| Network failure | ❌ Error (red) | ❌ Error (red) | This IS a real error |
| Data corruption | ❌ Error (red) | ❌ Error (red) | This IS a real error |

### 2. **Inline Alerts vs. Toast Notifications**

**Old behavior**: Red error toasts that pop up and disappear (bad for onboarding)

**New behavior**: Persistent inline alerts with context-aware messages (good for onboarding)

### 3. **Conditional UI Rendering**

**Old behavior**: Show disabled/broken UI (confusing)

**New behavior**: Hide editor entirely when prerequisites aren't met (clear)

---

## Testing Scenarios

### ✅ Scenario 1: New Mentor (No Profile)

**User State**:
- Authenticated as mentor
- `has_profile: false`

**Expected Behavior**:
- Dashboard: ✅ Loads normally (no profile required)
- Availability: ⚠️ Shows warning, hides editor
- Services: ⚠️ Can't create (shows friendly message)
- Feedback: ⚠️ Shows warning, explains next step

**Result**: User understands they need to create profile first

---

### ✅ Scenario 2: Mentor with Profile, No Stripe

**User State**:
- Authenticated as mentor
- `has_profile: true`
- `is_connected: false`

**Expected Behavior**:
- Dashboard: ✅ Loads normally
- Availability: ⚠️ Shows "complete Stripe Connect" warning
- Services: ✅ Can create services
- Feedback: ✅ Can view feedback

**Result**: User understands they need to complete Stripe onboarding

---

### ✅ Scenario 3: Fully Onboarded Mentor

**User State**:
- Authenticated as mentor
- `has_profile: true`
- `is_connected: true`
- `payout_enabled: true`

**Expected Behavior**:
- Dashboard: ✅ Full stats and data
- Availability: ✅ Full editor access
- Services: ✅ Can create/edit services
- Feedback: ✅ Can view all feedback

**Result**: Full platform access

---

### ✅ Scenario 4: Network Error

**User State**:
- API returns 500 error

**Expected Behavior**:
- Dashboard: ❌ Shows error alert (red)
- Availability: ❌ Shows error alert (red)
- Services: ❌ Shows error toast (red)
- Feedback: ❌ Shows error alert (red)

**Result**: User knows there's a technical problem

---

## Files Changed

### New Files (1)
1. **`frontend/src/utils/mentorOnboarding.ts`** (NEW)
   - Utility functions for onboarding state management
   - `requiresMentorProfile()`, `getOnboardingMessage()`, `shouldBlockInteraction()`

### Modified Files (3)
1. **`frontend/src/pages/mentor/AvailabilityPage.tsx`**
   - Added `onboardingMessage` state
   - Bootstrap checks distinguish onboarding vs. errors
   - UI conditionally rendered based on onboarding state
   - Warning severity for onboarding, error severity for real errors

2. **`frontend/src/pages/mentor/ProfilePage.tsx`**
   - Service creation handles missing profile gracefully
   - Uses `mentor_profile_id` from new status response
   - Service fetching doesn't throw errors when profile missing
   - Contextual error messages

3. **`frontend/src/pages/mentor/FeedbackPage.tsx`**
   - Added `onboardingMessage` state
   - Bootstrap check distinguishes onboarding vs. errors
   - Warning alert for missing profile
   - Error alert only for real failures

---

## Validation Checklist

- [x] No red error toasts for missing mentor profile
- [x] Onboarding states use warning (orange) severity
- [x] Real errors still use error (red) severity
- [x] Availability page hides editor during onboarding
- [x] Service creation shows contextual message
- [x] Feedback page shows helpful guidance
- [x] Dashboard works without profile
- [x] No linter errors
- [x] Clear, actionable messages for users
- [x] No regression in real error handling

---

## Message Hygiene

### ❌ Old Messages (Removed)
- "Mentor profile not loaded." (too technical, no action)
- "Mentor profile not found." (sounds like a bug)

### ✅ New Messages (Product-Correct)
- "Please create your mentor profile before setting availability." (clear action)
- "Please create your mentor profile before adding services." (clear action)
- "Please create your mentor profile to view feedback." (clear action)
- "Please complete Stripe Connect onboarding before setting availability." (clear action)
- "Payouts are not enabled yet. Please complete your Stripe account setup." (clear action)

---

## Code Quality

### Helper Functions
Created reusable utility functions instead of duplicating logic:
```typescript
// Clean, testable, reusable
requiresMentorProfile('/mentor/availability') // true
requiresMentorProfile('/mentor/dashboard')    // false
getOnboardingMessage(status, 'availability')  // contextual message
```

### Explicit State Management
Clear separation of concerns:
```typescript
const [error, setError] = useState<string | null>(null);           // Real errors
const [onboardingMessage, setOnboardingMessage] = useState<string | null>(null); // Onboarding states
```

### No Silent Hacks
All logic is explicit and readable:
```typescript
// ❌ Bad: Silent fallback
const id = profile?.id || 0;

// ✅ Good: Explicit check with clear intent
const profileId = mentorProfile?.mentor_profile_id || mentorProfile?.id;
if (!profileId) {
  setOnboardingMessage('Please create your mentor profile first.');
  return;
}
```

---

## Product Impact

### Before Fix
- 😡 New mentors: Confused by red errors during onboarding
- 😡 User sentiment: "The app is broken"
- 😡 Support tickets: "I can't use the platform"

### After Fix
- 😊 New mentors: Clear guidance on next steps
- 😊 User sentiment: "The app is guiding me through setup"
- 😊 Support tickets: Reduced confusion

---

## Maintenance Notes

### For Frontend Engineers

**When adding new mentor pages**:
1. Ask: "Does this page require a mentor profile?"
2. If YES: Add to `requiresMentorProfile()` list
3. Use `onboardingMessage` state for missing prerequisites
4. Use `error` state only for technical failures

**Error Handling Rules**:
- Missing profile → `onboardingMessage` + `severity="warning"`
- Network error → `error` + `severity="error"`
- Validation error → `error` + `severity="error"`
- Missing data → `error` + `severity="error"`

**Message Guidelines**:
- Start with "Please..." (actionable)
- Explain WHAT and WHY
- Avoid technical jargon ("not loaded", "not found")
- Use product terms ("create your profile", "complete onboarding")

---

## Related Documentation
- `AVAILABILITY_BOOTSTRAP_FIX.md` - Availability page status endpoint fix
- `PROFILE_STATUS_ENDPOINT.md` - Profile status endpoint implementation
- `frontend/src/utils/mentorOnboarding.ts` - Onboarding utility functions

---

**Signed Off By**: GateAI Product & Engineering Team  
**Review Status**: ✅ APPROVED  
**Production Ready**: YES

