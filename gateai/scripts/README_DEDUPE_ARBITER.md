# Kernel Physical Arbiter: ResourceLock De-duplication Engine

## Purpose

This arbiter prepares the database for adding a physical `UNIQUE` constraint on:

```sql
UNIQUE(resource_type, resource_id)
```

**This is NOT a cleanup script.**  
**This is a physical arbitration engine.**

---

## Guarantees

✅ **Deterministic Results**  
- Same input → same output (always)
- Tie-breaking rules are explicit and immutable

✅ **Auditable Deletions**  
- Every deletion is logged with full context
- `--verbose` mode provides complete audit trail

✅ **Atomic Execution**  
- All deletions occur in a single transaction
- Partial execution is impossible

✅ **Production Survivability**  
- Environment gate prevents accidental execution
- Dry-run mode is the default
- Idempotent (safe to re-run)

✅ **Rollback Safety**  
- Transaction-based deletion
- No schema changes
- No side effects without explicit ACK

---

## Behavioral Contract

### 1️⃣ Environment Gate (MANDATORY)

The script will **NOT** run unless:

```bash
export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
```

If missing, the script exits immediately with:

```
❌ ENVIRONMENT GATE FAILED

Pre-migration snapshot required.
Please run:
    export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
```

**No soft warning. No fallback. Hard stop.**

---

### 2️⃣ Duplicate Detection Strategy

Duplicates are identified **ONLY** by:

```
(resource_type, resource_id)
```

Uses DB-level grouping (memory-efficient):

```python
.values("resource_type", "resource_id")
.annotate(count=Count("id"))
.filter(count__gt=1)
```

**Does NOT load entire table into memory.**

---

### 3️⃣ Deterministic Tie-Breaking

For each duplicate group:

```python
ORDER BY (expires_at DESC, id DESC)
```

**KEEP exactly ONE record:**
1. Highest `expires_at` wins
2. If tie → highest `id` wins

**ALL others are deleted.**

This is deterministic and replayable.

---

### 4️⃣ Execution Modes

#### Dry Run (DEFAULT)

```bash
python scripts/dedupe_resource_locks.py --dry-run
```

- Prints arbitration plan ONLY
- No deletion allowed
- Safe to run anytime

#### Execute Mode

```bash
export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
python scripts/dedupe_resource_locks.py --execute
```

- Performs physical deletion
- Requires environment gate
- Atomic transaction

---

### 5️⃣ Verbose Audit Mode

```bash
python scripts/dedupe_resource_locks.py --dry-run --verbose
```

Prints for every group:
- `resource_type`, `resource_id`
- `decision_id` of every deleted row
- `expires_at` of every deleted row
- `id` of every deleted row

**Printed in DELETE ORDER.**

This log is your future audit trail.

---

### 6️⃣ Atomic Deletion

All deletions are wrapped in:

```python
with transaction.atomic():
    # All deletions occur here
```

**Partial execution is forbidden.**

---

### 7️⃣ Safety Guarantees

- ✅ **Idempotent** (safe to re-run)
- ✅ **Deterministic** (same result every time)
- ✅ **Never deletes non-duplicate rows**
- ✅ **Never runs without snapshot acknowledgment**

---

### 8️⃣ Output Summary

On completion, prints:

- Number of duplicate groups found
- Total rows deleted (or would be deleted)
- Execution mode

---

## Usage Examples

### Step 1: Dry Run (Audit)

```bash
cd gateai
python scripts/dedupe_resource_locks.py --dry-run --verbose
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE: DRY RUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No deletions will be performed.
This is a simulation only.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELETION PLAN SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Duplicate groups found: 3
Total rows to delete: 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILED DELETION AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GROUP: APPOINTMENT :: 100
  WINNER: Lock ID 42 (expires_at=2026-01-06 12:00:00+00:00)
  DELETIONS:
    ├─ Lock ID 41
    │  ├─ decision_id: test:A:1
    │  ├─ expires_at: 2026-01-06 11:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 1

...
```

### Step 2: Take Snapshot

```bash
# PostgreSQL
pg_dump careerbridge > backup_before_dedupe.sql

# SQLite
cp db.sqlite3 db.sqlite3.backup
```

### Step 3: Acknowledge Snapshot

```bash
export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
```

### Step 4: Execute Deletion

```bash
python scripts/dedupe_resource_locks.py --execute --verbose
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE: EXECUTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  PHYSICAL DELETIONS WILL BE PERFORMED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

... (deletion plan) ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTING DELETIONS...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rows deleted: 5
Database is now ready for UNIQUE constraint.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5: Verify Idempotency

```bash
python scripts/dedupe_resource_locks.py --execute
```

**Output:**

```
✅ No duplicates found.
Database is ready for UNIQUE constraint.
```

---

## Testing

Run the test suite to verify arbiter behavior:

```bash
cd gateai
python scripts/test_dedupe_arbiter.py
```

**Expected Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KERNEL ARBITER TEST SUITE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

... (test execution) ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL TESTS PASSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The arbiter is production-ready.
```

---

## Rollback Plan

If something goes wrong:

### SQLite

```bash
# Stop services
./stop_services.sh

# Restore backup
cp db.sqlite3.backup db.sqlite3

# Restart services
./start_services.sh
```

### PostgreSQL

```bash
# Stop services
./stop_services.sh

# Restore backup
psql careerbridge < backup_before_dedupe.sql

# Restart services
./start_services.sh
```

---

## Next Steps (After Successful De-duplication)

Once the arbiter completes successfully, you can add the UNIQUE constraint:

### Migration File

```python
# decision_slots/migrations/XXXX_add_unique_constraint.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decision_slots', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='resourcelock',
            constraint=models.UniqueConstraint(
                fields=['resource_type', 'resource_id'],
                name='unique_resource_lock'
            ),
        ),
    ]
```

### Run Migration

```bash
cd gateai
python manage.py migrate
```

---

## Troubleshooting

### Error: Environment gate failed

**Problem:** `PRE_MIGRATION_SNAPSHOT_TAKEN` not set.

**Solution:**

```bash
export PRE_MIGRATION_SNAPSHOT_TAKEN=YES
```

### Error: Transaction rolled back

**Problem:** Deletion failed mid-transaction.

**Solution:**
1. Check the error message
2. Database is unchanged (atomic rollback)
3. Fix issue and re-run
4. Idempotency guarantees safety

### Error: No duplicates found (but you expect some)

**Problem:** Duplicates may have been deleted already.

**Solution:**
1. Verify with direct query:

```sql
SELECT resource_type, resource_id, COUNT(*)
FROM decision_slots_resourcelock
GROUP BY resource_type, resource_id
HAVING COUNT(*) > 1;
```

2. If clean → proceed to migration

---

## Architecture Notes

### Why Physical Delete?

- Allows immediate re-locking of same resource tuple
- Prevents soft-delete confusion
- Audit trail is in KernelAuditLog (not in ResourceLock status)

### Why Order By `expires_at DESC, id DESC`?

- Keeps the lock that's valid longest
- Deterministic tie-breaker (highest ID)
- Stable across multiple runs

### Why Atomic Transaction?

- All-or-nothing guarantee
- No partial state
- Safe rollback on error

---

## Contact

For questions or issues:
- Check GateAI OS Contract: `docs/GATEAI_OS_CONTRACT.md`
- Review kernel primitives: `kernel/lock_primitives.py`
- File issue with `[KERNEL]` prefix

---

**KERNEL ARBITER v1.0**  
**Production-Ready | Auditable | Deterministic**

