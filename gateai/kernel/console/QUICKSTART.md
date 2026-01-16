# Kernel Console - Quick Start Guide

**Version**: 1.0.0  
**Status**: ✅ Production Ready

## Overview

The Kernel Console is the root control plane for GateAI OS. It provides superuser-only access to kernel-level operations, feature flag management, and system observability.

## Prerequisites

- Superuser account (is_superuser=True)
- Server running on port 8001 (or your configured port)
- Valid JWT token or active session

## Quick Test

### 1. Login as Superuser

```bash
# Get JWT token
curl -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "YOUR_SUPERUSER_USERNAME",
    "password": "YOUR_PASSWORD"
  }'

# Extract the access token from the response (DO NOT use <> brackets)
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Test Kernel Console Endpoints

#### Check Kernel Status

```bash
curl -X GET http://localhost:8001/kernel/console/status/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "governance_version": 1,
  "platform_state": "SINGLE_WORKLOAD",
  "active_workloads": ["PEER_MOCK"],
  "frozen_modules": [],
  "kernel_online": true,
  "world": "kernel"
}
```

#### View Feature Flags

```bash
curl -X GET http://localhost:8001/kernel/console/flags/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**: Array of feature flag objects

#### View World Map

```bash
curl -X GET http://localhost:8001/kernel/console/world-map/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "worlds": {
    "public": ["/", "/login", ...],
    "app": ["/app", "/dashboard", ...],
    "admin": ["/admin", ...],
    "kernel": ["/kernel", "/kernel/console", ...]
  },
  "current_world": "kernel"
}
```

#### List Superusers

```bash
curl -X GET http://localhost:8001/kernel/console/users/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**: Array of superuser accounts

#### Update Feature Flags

```bash
curl -X POST http://localhost:8001/kernel/console/flags/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "PEER_MOCK": "ON",
    "MENTORS": "BETA"
  }'
```

**Expected Response**:
```json
{
  "status": "updated"
}
```

## Security Verification

### Test 1: Non-superuser should be denied

```bash
# Login as regular user
curl -X POST http://localhost:8001/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "regular_user",
    "password": "password"
  }'

# Try to access kernel console (should return 403)
curl -X GET http://localhost:8001/kernel/console/status/ \
  -H "Authorization: Bearer $REGULAR_USER_TOKEN"
```

**Expected**: HTTP 403 Forbidden

### Test 2: Unauthenticated should be denied

```bash
# Try to access without token (should return 403)
curl -X GET http://localhost:8001/kernel/console/status/
```

**Expected**: HTTP 403 Forbidden

## Feature Flag States

- **OFF**: Feature is disabled, returns 404
- **BETA**: Feature is enabled only for superusers
- **ON**: Feature is enabled based on visibility settings

## Visibility Levels

- **internal**: Only superusers
- **staff**: Staff and above
- **user**: Authenticated users
- **public**: Everyone

## Troubleshooting

### Issue: Getting 403 Forbidden

**Check**:
1. Verify user is superuser: `user.is_superuser == True`
2. Verify JWT token is valid
3. Check GovernanceMiddleware is enabled in MIDDLEWARE
4. Verify path starts with `/kernel/console/`

### Issue: Getting 401 Unauthorized

**Check**:
1. JWT token is included in Authorization header
2. Token has not expired
3. Token format is: `Authorization: Bearer <token>`

### Issue: Middleware logs "Kernel access denied"

**Check**:
1. User account has `is_superuser=True`
2. User is authenticated
3. Request path matches kernel world namespace

## Testing

Run automated tests:

```bash
cd gateai
python3 manage.py test kernel.console.test_console --settings=gateai.settings_test
```

**Expected**: All 12 tests should pass

## Architecture

```
Request Flow:
1. Request → GovernanceMiddleware
2. Middleware checks: authenticated + superuser + kernel world
3. If authorized → bypass governance → route to console view
4. View checks: KernelPermission (double-layer security)
5. Execute console operation
6. Return response

Security Layers:
- Layer 1: GovernanceMiddleware (returns 403 if not authorized)
- Layer 2: KernelPermission (DRF permission class)
- Layer 3: JWT/Session authentication
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kernel/console/status/` | GET | Platform and kernel status |
| `/kernel/console/flags/` | GET | List all feature flags |
| `/kernel/console/flags/` | POST | Update feature flags |
| `/kernel/console/world-map/` | GET | 4-World OS namespace map |
| `/kernel/console/users/` | GET | List superuser accounts |

## Next Steps

After verifying the kernel console works:

1. ✅ Kernel console implemented and tested
2. 🔄 Build frontend control panel (optional)
3. 🔄 Add kernel metrics dashboard (Phase B)
4. 🔄 Add audit log query interface (Phase B)
5. 🔄 Add emergency kill switches (Phase B)

## Support

For issues or questions, check:
- `/gateai/kernel/KERNEL_CONSOLE_IMPLEMENTATION.md` - Full implementation doc
- `/gateai/kernel/console/test_console.py` - Test suite examples
- Server logs for "Kernel access denied" messages

---

**GateAI Kernel Console v1.0.0** - Root Shell Operational ✅
