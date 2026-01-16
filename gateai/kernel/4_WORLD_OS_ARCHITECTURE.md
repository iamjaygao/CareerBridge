# 4-World OS Architecture

## Overview

GateAI now implements a formal 4-world operating system model that provides clear namespace separation, security boundaries, and governance control.

This is an **OS-grade architecture upgrade**, not a UI permission change.

## World Constitution

### 1. PUBLIC World
**Purpose:** Marketing, landing pages, unauthenticated access

**Namespaces:**
- `/` (homepage)
- `/login`, `/register`
- `/about`, `/contact`, `/pricing`
- `/api/public`
- Public mentor browsing
- Assessment pages
- `/become-a-mentor`
- Email verification

**Security:**
- No authentication required
- Feature flags apply
- Read-only for most operations

### 2. APP World
**Purpose:** User workloads (students, mentors, authenticated app features)

**Namespaces:**
- `/app`
- `/student`, `/mentor`
- `/dashboard`, `/profile`, `/settings`
- `/appointments`, `/resumes`, `/chat`, `/notifications`
- `/api/app`
- `/api/v1/users/`
- `/api/v1/appointments/`
- `/api/v1/chat/`
- `/api/v1/search/`
- `/api/v1/signal-delivery/`
- `/api/v1/ats-signals/`

**Security:**
- Authentication required (`is_authenticated`)
- Feature flags apply
- Tenant/workspace isolation applies
- Role-based permissions (student/mentor)

### 3. ADMIN World
**Purpose:** Userland administration (staff, product operations)

**Namespaces:**
- `/admin`
- `/staff`
- `/api/admin`
- `/api/v1/adminpanel/` (general admin operations, NOT governance)
- `/analytics`

**Security:**
- Requires `is_staff=True`
- Feature flags apply
- Capability-based permissions (see `AdminCapability` model)
- Can modify user data, approve mentors, manage content

**Key Principle:**
- ADMIN is for **product operations**, NOT kernel control
- Staff admins CANNOT modify governance or kernel state

### 4. KERNEL World
**Purpose:** OS control plane (superuser only, immune to feature flags)

**Namespaces:**
- `/kernel`
- `/superadmin`
- `/api/engines`
- `/api/v1/adminpanel/governance` (governance APIs only)

**Security:**
- Requires `is_superuser=True` (hard gate, always enforced)
- IMMUNE to all feature flags
- IMMUNE to tenant gating
- IMMUNE to admin-level permissions
- Can modify platform state, feature flags, governance rules

**Key Principle:**
- Kernel world is the **root of trust**
- Only superusers can access
- Nothing can block or gate kernel operations

## Implementation

### Core Module: `kernel/worlds.py`

Defines the world namespace boundaries and resolution logic:

```python
WORLD_NAMESPACES = {
    "public": [...],
    "app": [...],
    "admin": [...],
    "kernel": [...]
}

def resolve_world(path: str) -> str:
    """Resolve which world a request path belongs to"""
    # Priority order: kernel > admin > app > public
```

### Middleware: `kernel/governance/middleware.py`

The `GovernanceMiddleware` now:

1. **Resolves world** for every request:
   ```python
   world = resolve_world(request.path)
   request.world = world  # Attach for downstream use
   ```

2. **Kernel Sovereign Guard** (runs first):
   ```python
   if is_kernel_world(world):
       if not user.is_superuser:
           return JsonResponse({'detail': 'Kernel access denied'}, status=403)
       # BYPASS ALL governance checks
       return self.get_response(request)
   ```

3. **Userland Governance** (runs for public/app/admin only):
   - Feature flag checks
   - Visibility rules
   - BETA feature gates
   - Module freezing

### Audit Logging

All audit logs now include the `world` field:

**Models updated:**
- `AdminAction` (adminpanel): `world` field added
- `GovernanceAudit` (kernel): `world` field added

**Helper functions:**
- `log_admin_action(request, ...)` automatically extracts `world` from `request.world`
- All governance API endpoints attach `world` to audit entries

## Routing Rules

### Landing Page Routing (Post-Login)

After successful login, users are redirected based on **Django authentication flags first**, then role:

1. **Priority 1: `is_superuser=True`** → `/superadmin` (kernel world)
2. **Priority 2: `is_staff=True` (but not superuser)** → `/admin` (admin world)
3. **Priority 3: Role field** → `/student`, `/mentor`, etc. (app world)

This ensures superusers always land in the kernel control plane, while staff admins land in the userland admin dashboard.

## Governance Rules

### Feature Flags Apply ONLY to Userland

Feature flags can control:
- PUBLIC: Public feature visibility
- APP: User workload features (appointments, chat, resume matcher, etc.)
- ADMIN: Admin panel features (user management, analytics, exports)

Feature flags CANNOT control:
- KERNEL: Governance APIs, engine management, OS observability

### State Transitions

**OFF:**
- Returns HTTP 404 for everyone in userland
- Kernel unaffected

**BETA:**
- Only superusers can access (in userland)
- Kernel unaffected

**ON:**
- Access based on visibility rules (public/user/staff/internal)
- Kernel unaffected

## Security Model

### Access Matrix

| World    | Auth Required | Min Permission | Feature Flags | Tenant Gating |
|----------|---------------|----------------|---------------|---------------|
| PUBLIC   | No            | None           | Yes           | No            |
| APP      | Yes           | Authenticated  | Yes           | Yes           |
| ADMIN    | Yes           | is_staff       | Yes           | No            |
| KERNEL   | Yes           | is_superuser   | **IMMUNE**    | **IMMUNE**    |

### Kernel Sovereignty

The kernel world has **absolute priority**:

1. Kernel paths are checked FIRST, before any other middleware logic
2. Kernel access gate is **hard-coded** (not configurable via feature flags)
3. Kernel bypasses:
   - All feature flag checks
   - All tenant/workspace gating
   - All admin capability checks
   - All rollout rules
4. Only `is_superuser=True` can enter kernel

This ensures the kernel control plane remains **always accessible** to root users, even if:
- All features are frozen
- Platform is in maintenance mode
- Governance rules are misconfigured
- Database is partially corrupted

## Migration Path

### Database Migrations

Run:
```bash
cd gateai
python3 manage.py migrate
```

This adds:
- `adminpanel.AdminAction.world` (CharField, default='admin')
- `kernel.GovernanceAudit.world` (CharField, default='kernel')

### Code Changes Required

**Existing admin action logging:**

Before:
```python
AdminAction.objects.create(
    admin_user=request.user,
    action_type='user_management',
    action_description='...',
    target_model='User',
    target_id=user.id,
    action_data={...},
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)
```

After (recommended):
```python
log_admin_action(
    request,
    action_type='user_management',
    action_description='...',
    target_model='User',
    target_id=user.id,
    action_data={...}
)
```

The helper automatically extracts `world` from `request.world`.

## Testing

### Manual Testing

1. **Test kernel sovereignty:**
   ```bash
   # As superuser
   curl -H "Authorization: Bearer $SUPERUSER_TOKEN" http://localhost:8001/superadmin/
   # Should return 200
   
   # As staff admin (non-superuser)
   curl -H "Authorization: Bearer $STAFF_TOKEN" http://localhost:8001/superadmin/
   # Should return 403: Kernel access denied
   ```

2. **Test world resolution:**
   ```python
   from kernel.worlds import resolve_world
   
   assert resolve_world('/superadmin/governance') == 'kernel'
   assert resolve_world('/admin/users') == 'admin'
   assert resolve_world('/student/dashboard') == 'app'
   assert resolve_world('/login') == 'public'
   ```

3. **Test audit logging:**
   ```bash
   # Make a governance change as superuser
   # Check GovernanceAudit.objects.last().world == 'kernel'
   
   # Make an admin action as staff
   # Check AdminAction.objects.last().world == 'admin'
   ```

### Automated Testing

Create test suite in `kernel/tests/test_worlds.py`:

```python
from django.test import TestCase, RequestFactory
from kernel.worlds import resolve_world
from kernel.governance.middleware import GovernanceMiddleware

class WorldArchitectureTest(TestCase):
    def test_world_resolution(self):
        """Test path to world resolution"""
        ...
    
    def test_kernel_sovereign_gate(self):
        """Test kernel access control"""
        ...
    
    def test_userland_feature_flags(self):
        """Test feature flags apply to userland only"""
        ...
```

## Operational Notes

### Monitoring

All requests now have `request.world` attached. Add to observability:

- **Logging:** Include `world` in all structured logs
- **Metrics:** Track request counts by world
- **Tracing:** Tag spans with world context

Example log format:
```json
{
  "timestamp": "2026-01-13T21:51:00Z",
  "level": "INFO",
  "world": "kernel",
  "path": "/api/v1/adminpanel/governance/platform-state/",
  "user": "root",
  "status": 200
}
```

### Governance Operations

When managing feature flags:

1. **Freezing userland features:** Set flag state to `OFF`
   - This affects public/app/admin worlds
   - Kernel remains unaffected

2. **Maintenance mode:** Update `PlatformState.state = 'MAINTENANCE'`
   - Can freeze all userland modules
   - Kernel governance APIs remain accessible to superusers

3. **Emergency access:** If governance rules break:
   - Superuser can always access `/superadmin`
   - Can reset feature flags, unfreeze modules
   - No userland operation can lock out kernel

## Future Work

### Phase 2: Multi-Tenancy

Extend world model to support tenant isolation:

```python
def resolve_world(path: str, tenant_id: str = None) -> str:
    # Tenant-aware world resolution
    # e.g., /app/{tenant_id}/dashboard
```

### Phase 3: World-Specific Middleware Stack

Allow different middleware configurations per world:

```python
WORLD_MIDDLEWARE = {
    'public': ['CorsMiddleware', 'RateLimitMiddleware'],
    'app': ['AuthMiddleware', 'TenantMiddleware', 'FeatureFlagMiddleware'],
    'admin': ['AuthMiddleware', 'StaffCheckMiddleware', 'AuditMiddleware'],
    'kernel': ['AuthMiddleware', 'SuperUserCheckMiddleware'],
}
```

### Phase 4: World-Specific Rate Limits

Kernel operations should have separate (higher) rate limits:

```python
RATE_LIMITS = {
    'public': '100/hour',
    'app': '1000/hour',
    'admin': '5000/hour',
    'kernel': 'unlimited',
}
```

## FAQ

**Q: Can staff admins access `/admin` after this change?**

A: Yes. Staff admins (`is_staff=True`) can access `/admin` normally. The kernel guard only blocks access to `/superadmin` and governance APIs.

**Q: What happens if I set a feature flag to OFF that includes a kernel path?**

A: Feature flags are ignored for kernel world. Kernel paths are IMMUNE to feature flag state.

**Q: Can I use feature flags to temporarily block admin access?**

A: Yes, you can create feature flags for admin-world paths (e.g., `/api/admin/users`). These flags will only affect admin world; kernel world bypasses them.

**Q: How do I add a new namespace to a world?**

A: Update `WORLD_NAMESPACES` in `kernel/worlds.py`. No other changes needed (middleware auto-resolves).

**Q: What if two worlds have overlapping paths?**

A: The resolver uses priority order: `kernel > admin > app > public`. The most specific/restrictive world wins.

## Summary

The 4-World OS Architecture provides:

✅ **Clear boundaries:** Each world has distinct namespaces and purposes  
✅ **Kernel sovereignty:** Superusers always have access to OS control plane  
✅ **Feature flag immunity:** Kernel cannot be gated by userland governance  
✅ **Audit trails:** All operations tagged with world context  
✅ **Role-based routing:** Post-login redirects respect world boundaries  
✅ **Scalable:** Easy to add new namespaces or worlds in the future  

This is a foundational upgrade that enables safe, deterministic, and auditable platform operations.
