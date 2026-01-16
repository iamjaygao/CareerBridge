# 4-World OS Entry Constitution

**Status:** ✅ RATIFIED  
**Date:** 2026-01-13  
**Effective:** Immediately

---

## Preamble

This document establishes the sovereign entry points for the 4-World OS Architecture and eliminates all illegal automatic redirects. Each world is born with equal standing, and the PUBLIC world reclaims its rightful ownership of the root path `/`.

## Article I: World Sovereignty

### Section 1.1 — World Entry Points

Each world SHALL have ONE and ONLY ONE sovereign entry point:

| World    | Entry Point    | Description                           |
|----------|----------------|---------------------------------------|
| PUBLIC   | `/`            | Marketing, landing, unauthenticated   |
| APP      | `/app`         | User workloads (authenticated)        |
| ADMIN    | `/admin`       | Userland administration (staff)       |
| KERNEL   | `/superadmin`  | OS control plane (superuser only)     |

### Section 1.2 — Entry Point Guarantees

1. **Uniqueness:** No world may be reachable via another world's entry point.
2. **Permanence:** Entry points SHALL NOT be changed without constitutional amendment.
3. **Accessibility:** Each entry point SHALL render its world's landing page directly, without intermediate redirects.

## Article II: PUBLIC World Sovereignty

### Section 2.1 — ROOT Path Ownership

The PUBLIC world is hereby granted EXCLUSIVE and PERPETUAL ownership of the root path `/`.

**Guaranteed Rights:**
- `/` SHALL render the public landing page (marketing, value proposition)
- `/` SHALL be accessible to ALL visitors (authenticated or not)
- `/` SHALL NEVER auto-redirect to any other world

### Section 2.2 — Prohibited Actions

The following actions are STRICTLY FORBIDDEN and constitute violations of this constitution:

```typescript
// ❌ ILLEGAL
if (isAuthenticated) {
  navigate('/admin');        // VIOLATION: Forced redirect from PUBLIC to ADMIN
  navigate('/dashboard');    // VIOLATION: Forced redirect from PUBLIC to APP
  navigate('/superadmin');   // VIOLATION: Forced redirect from PUBLIC to KERNEL
}

// ✅ LEGAL
// Let users browse PUBLIC world regardless of auth state
// Provide navigation links to their world if authenticated
```

### Section 2.3 — User Choice Principle

Authenticated users visiting `/` SHALL be presented with:
- The public landing page (no redirect)
- A visible navigation link to "My World" (their assigned world)
- Full freedom to browse public content before entering their world

## Article III: Login World Dispatcher

### Section 3.1 — Post-Login Routing

After successful authentication, users SHALL be dispatched to their world according to this STRICT priority:

```typescript
function dispatchToWorld(user: User): string {
  // Priority 1: Kernel sovereignty
  if (user.is_superuser) {
    return '/superadmin';  // KERNEL world
  }
  
  // Priority 2: Admin world
  if (user.is_staff) {
    return '/admin';  // ADMIN world
  }
  
  // Priority 3: App world (role-based)
  if (user.role === 'mentor') {
    return '/mentor';  // APP world (mentor variant)
  }
  
  if (user.role === 'student') {
    return '/student';  // APP world (student variant)
  }
  
  // Priority 4: Default app entry
  return '/app';  // APP world (generic)
}
```

### Section 3.2 — Dispatcher Exclusivity

This dispatcher is the ONLY authorized mechanism for post-login world assignment. NO other code path may redirect users to worlds based on authentication state.

### Section 3.3 — Intercepted Routes

If a user was intercepted while trying to access a protected route, the post-login redirect SHALL honor the original destination:

```typescript
const redirectTo = location.state?.redirectTo || dispatchToWorld(user);
navigate(redirectTo, { replace: true });
```

## Article IV: Kernel Entry Protection

### Section 4.1 — Kernel Sovereignty

The KERNEL world entry `/superadmin` is the MOST PROTECTED entry point:

1. **Hard Gate:** ONLY `is_superuser=True` may access
2. **Non-SPA:** `/superadmin` SHALL NOT be wrapped by app-level route guards
3. **Middleware Guard:** Access control enforced by `GovernanceMiddleware` (backend)
4. **Immune:** Kernel world is IMMUNE to feature flags, tenant gating, and all userland governance

### Section 4.2 — Access Denial

Non-superusers attempting to access `/superadmin` SHALL receive:
- HTTP 403 Forbidden
- Clear error message: "Kernel access denied"
- NO fallback redirect to other worlds

## Article V: Implementation Requirements

### Section 5.1 — Frontend Implementation

**File:** `frontend/src/pages/home/LandingPage.tsx`

```typescript
// ✅ COMPLIANT
const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  
  // NO automatic redirect for authenticated users
  // Public world owns "/" - let users browse freely
  
  return (
    <Box>
      {/* Render public landing page content */}
    </Box>
  );
};
```

**File:** `frontend/src/pages/auth/LoginPage.tsx`

```typescript
// ✅ COMPLIANT
const onSubmit = async (data: LoginFormData) => {
  const result = await dispatch(loginUser(data)).unwrap();
  const user = result.user;
  
  // LOGIN WORLD DISPATCHER (Article III)
  const landingPath = getLandingPathByRole(user);
  const redirectTo = location.state?.redirectTo || landingPath;
  
  navigate(redirectTo, { replace: true });
};
```

**File:** `frontend/src/components/layout/PublicHeader.tsx`

```typescript
// ✅ COMPLIANT
// Authenticated users see "My World" button
const getUserWorldPath = (): string => {
  if (!user) return '/';
  return getLandingPathByRole(user);
};

<MenuItem onClick={() => handleNavigation(getUserWorldPath())}>
  <Dashboard sx={{ mr: 2, fontSize: 20 }} />
  My World
</MenuItem>
```

### Section 5.2 — Backend Implementation

**File:** `gateai/kernel/governance/middleware.py`

```python
# ✅ COMPLIANT
class GovernanceMiddleware:
    def __call__(self, request):
        # Resolve world
        world = resolve_world(request.path)
        request.world = world
        
        # KERNEL SOVEREIGN GUARD (Article IV)
        if is_kernel_world(world):
            if not request.user.is_superuser:
                return JsonResponse({'detail': 'Kernel access denied'}, status=403)
            # Bypass all governance
            return self.get_response(request)
        
        # Userland governance
        # ...
```

**No LOGIN_REDIRECT_URL:** Django SHALL NOT define automatic login redirects. The frontend LOGIN WORLD DISPATCHER (Article III) is the sole authority.

## Article VI: Testing & Validation

### Section 6.1 — Required Tests

The following tests SHALL pass before this constitution is considered ratified:

1. **PUBLIC World Ownership**
   ```bash
   # Open localhost:3000
   # Should show public landing page (not redirect)
   # Works for both authenticated and unauthenticated users
   ```

2. **Login World Dispatcher**
   ```bash
   # Login as superuser → redirects to /superadmin ✓
   # Login as staff → redirects to /admin ✓
   # Login as student → redirects to /student ✓
   # Login as mentor → redirects to /mentor ✓
   ```

3. **Kernel Entry Protection**
   ```bash
   # Superuser can access /superadmin → 200 OK ✓
   # Staff admin tries /superadmin → 403 Forbidden ✓
   # Regular user tries /superadmin → 403 Forbidden ✓
   ```

4. **User Choice Principle**
   ```bash
   # Authenticated user visits localhost:3000 → sees landing page ✓
   # User clicks "My World" → navigates to their world ✓
   # User can browse public pages without forced redirect ✓
   ```

### Section 6.2 — Compliance Checklist

- [ ] `/` renders public landing page (no auto-redirect)
- [ ] Authenticated users can browse `/` freely
- [ ] "My World" navigation link present for authenticated users
- [ ] LoginPage uses `getLandingPathByRole(user)`
- [ ] Superusers land on `/superadmin` after login
- [ ] Staff (non-superuser) land on `/admin` after login
- [ ] Students/mentors land on their respective paths
- [ ] Non-superusers get 403 on `/superadmin` access
- [ ] Kernel world bypasses all feature flags
- [ ] No `LOGIN_REDIRECT_URL` in Django settings

## Article VII: Violations & Penalties

### Section 7.1 — Code Review Requirements

ALL pull requests modifying routing or authentication MUST:
1. Cite this constitution in the PR description
2. Demonstrate compliance with world entry guarantees
3. Include tests validating the 4 world entry points

### Section 7.2 — Prohibited Patterns

The following code patterns are BANNED:

```typescript
// ❌ BANNED PATTERN 1: Auto-redirect from "/"
React.useEffect(() => {
  if (isAuthenticated) {
    navigate('/dashboard');  // VIOLATION
  }
}, [isAuthenticated]);

// ❌ BANNED PATTERN 2: Unconditional world switch on PUBLIC paths
if (user && window.location.pathname === '/') {
  window.location.href = '/admin';  // VIOLATION
}

// ❌ BANNED PATTERN 3: Backend redirect to specific world
# Django settings.py
LOGIN_REDIRECT_URL = '/admin'  # VIOLATION (must use frontend dispatcher)
```

## Article VIII: World Navigation Matrix

### Section 8.1 — Valid Navigation Paths

This matrix defines LEGAL navigation between worlds:

| From → To     | PUBLIC | APP    | ADMIN  | KERNEL |
|---------------|--------|--------|--------|--------|
| **PUBLIC**    | ✅     | 🔒     | 🔒     | 🔒     |
| **APP**       | ✅     | ✅     | ❌     | ❌     |
| **ADMIN**     | ✅     | ❌     | ✅     | ❌     |
| **KERNEL**    | ✅     | ✅     | ✅     | ✅     |

Legend:
- ✅ Always allowed
- 🔒 Allowed after authentication
- ❌ Never allowed (403)

### Section 8.2 — Navigation Rules

1. **PUBLIC → Any World:** Must authenticate first
2. **APP → ADMIN:** Forbidden (role separation)
3. **ADMIN → APP:** Forbidden (role separation)
4. **KERNEL → Any World:** Allowed (superuser omnipotence)
5. **Any World → PUBLIC:** Always allowed

## Article IX: Future Amendments

### Section 9.1 — Amendment Process

This constitution may be amended ONLY through:
1. Written proposal with rationale
2. Review by system architects
3. Unanimous approval
4. Full regression testing
5. Documentation update

### Section 9.2 — Non-Amendable Provisions

The following provisions SHALL NOT be amended:

1. **PUBLIC world ownership of `/`** (Article II.1)
2. **Kernel sovereignty principles** (Article IV.1)
3. **Login dispatcher exclusivity** (Article III.2)

## Article X: Effective Date & Transition

### Section 10.1 — Immediate Effect

This constitution takes effect IMMEDIATELY upon ratification.

### Section 10.2 — Legacy Code Cleanup

All code violating this constitution SHALL be remediated within:
- **Critical violations (auto-redirect from "/"):** Immediate (same day)
- **High violations (broken world dispatcher):** 1 week
- **Medium violations (unclear navigation):** 2 weeks

## Ratification

This constitution is hereby RATIFIED as the governing law of the GateAI 4-World OS Architecture.

**Signed:**  
GateAI OS Architect  
Date: 2026-01-13

---

## Appendix A: Quick Reference

### World Entry Points (One-Liner)
```
PUBLIC: /   |  APP: /app   |  ADMIN: /admin   |  KERNEL: /superadmin
```

### Post-Login Dispatcher (One-Liner)
```typescript
is_superuser ? '/superadmin' : is_staff ? '/admin' : role_path
```

### Key Guarantees
1. `/` always shows public landing (no redirect)
2. Only login dispatcher may send users to worlds
3. Kernel entry protected by hard gate (superuser only)
4. Users can browse PUBLIC world regardless of auth state

---

**End of Constitution**
