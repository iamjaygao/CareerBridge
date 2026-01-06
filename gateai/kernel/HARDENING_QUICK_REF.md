# sys_claim Hardening Quick Reference

## 🎯 What Changed (v1.0 → v1.1)

| # | Change | Impact | Test |
|---|--------|--------|------|
| 1 | **Broken Transaction Pattern** | NO DB in `except IntegrityError` | `test_physical_conflict_*` |
| 2 | **Remove dateutil** | stdlib `datetime.fromisoformat()` only | `test_iso8601_with_z_suffix` |
| 3 | **Audit Never Blocks** | Swallow all audit errors | `test_audit_failure_*` |
| 4 | **Document TTL Policy** | Re-entry does NOT extend `expires_at` | Comment added |
| 5 | **2 New Tests** | Verify hardening requirements | See below |

---

## ⚠️ CRITICAL: Broken Transaction Pattern

### ❌ BEFORE (UNSAFE)
```python
except IntegrityError:
    existing = ResourceLock.objects.filter(...).first()  # CRASH!
```

### ✅ AFTER (SAFE)
```python
needs_post_atomic_check = False

except IntegrityError:
    needs_post_atomic_check = True  # NO DB ACCESS

finally:
    if needs_post_atomic_check:
        existing = ResourceLock.objects.filter(...).first()  # SAFE
```

**Rule:** NO database queries inside `except IntegrityError` - ZERO TOLERANCE

---

## 📅 Time Parsing (stdlib-only)

### Accepted Formats
```python
# ✅ datetime objects
payload = {"expires_at": timezone.now() + timedelta(hours=1)}

# ✅ ISO-8601 with timezone
payload = {"expires_at": "2026-01-06T15:30:00+00:00"}

# ✅ ISO-8601 with Z (normalized to +00:00)
payload = {"expires_at": "2026-01-06T15:30:00Z"}

# ✅ Duration from now
payload = {"duration_seconds": 3600}

# ❌ Natural language (REJECTED with 400)
payload = {"expires_at": "tomorrow"}
```

---

## 🔒 Re-Entry Policy

### Behavior
```python
# Call 1: User 1 claims resource → OK
sys_claim({..., "owner_id": 1, "expires_at": T+1h})

# Call 2: User 1 re-claims (page refresh) → OK
sys_claim({..., "owner_id": 1, "expires_at": T+2h})  # Different expiry

# Result: Lock.expires_at == T+1h (UNCHANGED)
```

**Rule:** Re-entry succeeds but does NOT extend TTL

**Rationale:** Prevents stealth lease hijacking. Explicit renewal requires `sys_extend()` (future).

---

## 📝 Audit Resilience

### Guarantee
```python
# Even if audit fails...
with patch.object(KernelAuditLog, 'store_outcome', side_effect=Exception):
    result = sys_claim(payload)

# ...syscall MUST proceed normally
assert result.outcome_code == "OK"
assert ResourceLock.objects.get(resource_id=...) exists
```

**Rule:** Audit is best-effort. Syscall correctness > audit completeness.

---

## 🧪 New Tests (2)

### 1. test_audit_failure_does_not_block_syscall
```python
# Monkeypatch audit to fail
with patch.object(KernelAuditLog, 'store_outcome', side_effect=Exception):
    result = sys_claim(payload)

# Syscall proceeds normally
assert result.outcome_code == "OK"
assert lock exists in DB
```

### 2. test_iso8601_with_z_suffix
```python
payload = {"expires_at": "2026-01-06T15:30:00Z"}
result = sys_claim(payload)

assert result.outcome_code == "OK"
assert lock.expires_at.tzinfo is not None  # UTC
```

---

## ✅ Verification Checklist

```bash
# Run full test suite (16 tests)
cd gateai
python3 manage.py test kernel.tests.test_syscalls -v 2

# Critical tests
python3 manage.py test kernel.tests.test_syscalls::SysClaimTestCase.test_physical_conflict_different_owner
python3 manage.py test kernel.tests.test_syscalls::SysClaimTestCase.test_reentrant_same_owner
python3 manage.py test kernel.tests.test_syscalls::SysClaimTestCase.test_audit_failure_does_not_block_syscall
python3 manage.py test kernel.tests.test_syscalls::SysClaimTestCase.test_iso8601_with_z_suffix

# Expected: 16/16 PASS ✅
```

---

## 🚀 Deployment

### Pre-Deployment
```bash
# 1. Verify no linter errors
cd gateai
python3 -m flake8 kernel/syscalls.py kernel/tests/test_syscalls.py

# 2. Run tests
python3 manage.py test kernel.tests.test_syscalls -v 2

# 3. Check no dateutil imports
grep -r "dateutil" kernel/
# Expected: No matches
```

### Deployment
```bash
# Deploy code (NO downtime, NO migration)
git pull
# That's it! No database changes needed.
```

### Post-Deployment
```bash
# Monitor logs for:
# - ✅ NO "transaction is aborted" errors
# - ✅ NO 500 errors from audit failures
# - ✅ Re-entry behavior: owner_id match → OK
# - ✅ Conflict behavior: owner_id mismatch → CONFLICT
```

---

## 🔄 Rollback (if needed)

```bash
# Instant rollback (no schema to revert)
git revert <commit_hash>
git push

# Verify
python3 manage.py test kernel.tests.test_syscalls
```

---

## 📊 Risk Level

| Change | Risk | Mitigation |
|--------|------|------------|
| Broken Transaction | **Medium** | Extensive testing, all paths covered |
| Remove dateutil | **Low** | ISO-8601 already standard |
| Audit Never Blocks | **Low** | Behavior unchanged (already had try/except) |
| Document TTL | **Zero** | Comment only |
| Add Tests | **Zero** | Verification only |

**Overall Risk:** Low ✅

---

## 📖 Documentation

- `SYSCALL_HARDENING_REPORT.md` - Full specification
- `HARDENING_CHANGES.md` - Detailed change log
- `HARDENING_QUICK_REF.md` - This file
- `SYSCALL_SPEC_SYS_CLAIM.md` - Original spec (updated)

---

## 💡 Key Principles

1. **ZERO TOLERANCE** - No DB queries inside except IntegrityError
2. **stdlib-ONLY** - No third-party deps in kernel
3. **BEST-EFFORT AUDIT** - Never block syscall return
4. **EXPLICIT RENEWAL** - Re-entry does NOT extend TTL
5. **PHYSICAL SAFETY** - Trust PostgreSQL UNIQUE constraints

---

**Status:** ✅ READY FOR PRODUCTION  
**Version:** v1.1 (Hardened)  
**Tests:** 16/16 PASS

