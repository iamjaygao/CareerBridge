# 🔄 Kernel Physical Arbiter: Visual Flow

## Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INVOKES ARBITER                        │
│   python scripts/dedupe_resource_locks.py [--dry-run|--execute] │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  1️⃣ ENVIRONMENT GATE CHECK                      │
│                                                                 │
│   if PRE_MIGRATION_SNAPSHOT_TAKEN != "YES":                    │
│       ❌ EXIT (Hard Stop)                                       │
│       Print: "Pre-migration snapshot required"                 │
│   else:                                                         │
│       ✅ PROCEED                                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              2️⃣ DUPLICATE DETECTION (DB-Level)                 │
│                                                                 │
│   SELECT resource_type, resource_id, COUNT(*)                  │
│   FROM decision_slots_resourcelock                             │
│   GROUP BY resource_type, resource_id                          │
│   HAVING COUNT(*) > 1                                          │
│                                                                 │
│   Result: List[(resource_type, resource_id, count)]            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                    ┌─────┴──────┐
                    │   Found    │
                    │ Duplicates?│
                    └─────┬──────┘
                   YES    │    NO
         ┌────────────────┼────────────────┐
         ▼                                 ▼
┌────────────────────┐           ┌─────────────────────┐
│  3️⃣ COMPUTE PLAN   │           │   ✅ NO ACTION      │
│                    │           │                     │
│  For each group:   │           │  Print: "No dupes"  │
│                    │           │  EXIT(0)            │
│  1. ORDER BY       │           └─────────────────────┘
│     -expires_at    │
│     -id            │
│                    │
│  2. winner = [0]   │
│     losers = [1:]  │
│                    │
│  3. Plan deletion  │
│     of losers      │
└────────┬───────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  4️⃣ PRINT DELETION PLAN                         │
│                                                                 │
│   Duplicate groups found: N                                     │
│   Total rows to delete: M                                       │
│                                                                 │
│   [--verbose] Detailed audit per deletion:                      │
│     - resource_type, resource_id                                │
│     - decision_id, expires_at, status, owner_id                 │
│     - winner_id, winner_expires_at                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                    ┌─────┴──────┐
                    │   Execution │
                    │     Mode?   │
                    └─────┬───────┘
               DRY-RUN    │    EXECUTE
         ┌────────────────┼────────────────┐
         ▼                                 ▼
┌────────────────────┐           ┌─────────────────────────────────┐
│  ✅ DRY-RUN DONE   │           │  5️⃣ ATOMIC EXECUTION             │
│                    │           │                                 │
│  No deletions      │           │  with transaction.atomic():     │
│  performed         │           │                                 │
│                    │           │    # Bulk delete                │
│  Print: "Run with │           │    ResourceLock.objects         │
│  --execute"        │           │      .filter(id__in=losers)     │
│                    │           │      .delete()                  │
│  EXIT(0)           │           │                                 │
└────────────────────┘           │  # All-or-nothing               │
                                 │  # Rollback on error            │
                                 └──────────┬──────────────────────┘
                                            │
                                   ┌────────┴─────────┐
                                   │   Success?       │
                                   └────────┬─────────┘
                                     YES    │    NO
                          ┌─────────────────┼────────────────┐
                          ▼                                  ▼
                 ┌────────────────────┐           ┌──────────────────┐
                 │  6️⃣ SUCCESS         │           │  ❌ FAILURE      │
                 │                    │           │                  │
                 │  Rows deleted: M   │           │  Transaction     │
                 │  Database ready    │           │  rolled back     │
                 │  for UNIQUE        │           │                  │
                 │  constraint        │           │  No changes made │
                 │                    │           │                  │
                 │  EXIT(0)           │           │  EXIT(1)         │
                 └────────────────────┘           └──────────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Deterministic Tie-Breaking Logic

```
Duplicate Group: (APPOINTMENT, resource_id=100)
─────────────────────────────────────────────────

Locks in DB:
┌────┬────────────┬────────────────────┬────────┬──────────┐
│ ID │ decision_id│ expires_at         │ status │ owner_id │
├────┼────────────┼────────────────────┼────────┼──────────┤
│ 41 │ test:A:1   │ 2026-01-06 11:00  │ active │    1     │
│ 42 │ test:A:2   │ 2026-01-06 12:00  │ active │    1     │ ← HIGHER expires_at
│ 43 │ test:A:3   │ 2026-01-06 11:00  │ active │    1     │
└────┴────────────┴────────────────────┴────────┴──────────┘

Step 1: ORDER BY expires_at DESC, id DESC
┌────┬────────────┬────────────────────┐
│ 42 │ test:A:2   │ 2026-01-06 12:00  │ ← WINNER (highest expires_at)
│ 43 │ test:A:3   │ 2026-01-06 11:00  │ ← DELETE
│ 41 │ test:A:1   │ 2026-01-06 11:00  │ ← DELETE
└────┴────────────┴────────────────────┘

Step 2: KEEP winner, DELETE losers
┌────┬────────────┬────────────────────┐
│ 42 │ test:A:2   │ 2026-01-06 12:00  │ ← RETAINED
└────┴────────────┴────────────────────┘

Result: UNIQUE(resource_type=APPOINTMENT, resource_id=100) ✅
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Tie-Breaking Edge Case (Same expires_at)

```
Duplicate Group: (APPOINTMENT, resource_id=200)
─────────────────────────────────────────────────

Locks in DB:
┌────┬────────────┬────────────────────┬────────┬──────────┐
│ ID │ decision_id│ expires_at         │ status │ owner_id │
├────┼────────────┼────────────────────┼────────┼──────────┤
│ 44 │ test:B:1   │ 2026-01-06 13:00  │ active │    2     │
│ 45 │ test:B:2   │ 2026-01-06 13:00  │ active │    2     │ ← SAME expires_at
└────┴────────────┴────────────────────┴────────┴──────────┘

Step 1: ORDER BY expires_at DESC, id DESC
┌────┬────────────┬────────────────────┐
│ 45 │ test:B:2   │ 2026-01-06 13:00  │ ← WINNER (highest ID)
│ 44 │ test:B:1   │ 2026-01-06 13:00  │ ← DELETE
└────┴────────────┴────────────────────┘

Step 2: KEEP winner, DELETE loser
┌────┬────────────┬────────────────────┐
│ 45 │ test:B:2   │ 2026-01-06 13:00  │ ← RETAINED
└────┴────────────┴────────────────────┘

Result: UNIQUE(resource_type=APPOINTMENT, resource_id=200) ✅
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Safety Gates

```
┌─────────────────────────────────────────────────────────────┐
│                    SAFETY GATE MATRIX                       │
├────────────────┬────────────────────────────────────────────┤
│ Gate           │ Enforcement                                │
├────────────────┼────────────────────────────────────────────┤
│ Environment    │ PRE_MIGRATION_SNAPSHOT_TAKEN=YES required │
│                │ Hard stop if missing                       │
├────────────────┼────────────────────────────────────────────┤
│ Default Mode   │ --dry-run (no deletions)                   │
├────────────────┼────────────────────────────────────────────┤
│ Explicit Flag  │ --execute required for deletions           │
├────────────────┼────────────────────────────────────────────┤
│ Transaction    │ Atomic (all-or-nothing)                    │
├────────────────┼────────────────────────────────────────────┤
│ Idempotency    │ Safe to re-run (deterministic)             │
├────────────────┼────────────────────────────────────────────┤
│ Rollback       │ Automatic on error                         │
├────────────────┼────────────────────────────────────────────┤
│ Audit Trail    │ --verbose logs every deletion              │
└────────────────┴────────────────────────────────────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Transaction Flow

```
BEGIN TRANSACTION
    │
    ├─> SELECT FOR UPDATE (implicit via filter)
    │   ├─> Lock ID 41
    │   ├─> Lock ID 43
    │   └─> Lock ID 46
    │
    ├─> DELETE WHERE id IN (41, 43, 46)
    │   ├─> Delete Lock 41 ✓
    │   ├─> Delete Lock 43 ✓
    │   └─> Delete Lock 46 ✓
    │
    └─> COMMIT
        │
        ├─> SUCCESS → All deletions permanent
        └─> ERROR   → ROLLBACK (no changes)

Atomicity Guarantee:
  - All deletions succeed → COMMIT
  - Any deletion fails   → ROLLBACK ALL
  - No partial state possible
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Verbose Output Example

```bash
$ python scripts/dedupe_resource_locks.py --execute --verbose
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODE: EXECUTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  PHYSICAL DELETIONS WILL BE PERFORMED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELETION PLAN SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Duplicate groups found: 3
Total rows to delete: 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETAILED DELETION AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GROUP: APPOINTMENT :: 100
  WINNER: Lock ID 42 (expires_at=2026-01-06 12:00:00+00:00)
  DELETIONS:
    ├─ Lock ID 41
    │  ├─ decision_id: test:A:1
    │  ├─ expires_at: 2026-01-06 11:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 1
    ├─ Lock ID 43
    │  ├─ decision_id: test:A:3
    │  ├─ expires_at: 2026-01-06 11:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 1

GROUP: APPOINTMENT :: 200
  WINNER: Lock ID 45 (expires_at=2026-01-06 13:00:00+00:00)
  DELETIONS:
    ├─ Lock ID 44
    │  ├─ decision_id: test:B:1
    │  ├─ expires_at: 2026-01-06 13:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 2

GROUP: STAGING_SERVER :: 300
  WINNER: Lock ID 48 (expires_at=2026-01-06 14:00:00+00:00)
  DELETIONS:
    ├─ Lock ID 46
    │  ├─ decision_id: test:C:1
    │  ├─ expires_at: 2026-01-06 12:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 3
    ├─ Lock ID 47
    │  ├─ decision_id: test:C:2
    │  ├─ expires_at: 2026-01-06 13:00:00+00:00
    │  ├─ status: active
    │  └─ owner_id: 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTING DELETIONS...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rows deleted: 5
Database is now ready for UNIQUE constraint.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Error Handling Flow

```
                  ┌──────────────┐
                  │   Execute    │
                  │   Arbiter    │
                  └──────┬───────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │Environment│ │Transaction│ │ General  │
     │ Gate Fail │ │   Error  │ │ Exception│
     └──────┬────┘ └─────┬────┘ └─────┬────┘
            │            │            │
            │            │            │
            ▼            ▼            ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │Print gate│ │Transaction│ │  Print   │
     │ message  │ │ ROLLBACK │ │  error   │
     └──────┬───┘ └─────┬────┘ └─────┬────┘
            │            │            │
            │            │            │
            └────────────┼────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   EXIT(1)    │
                  │              │
                  │ NO CHANGES   │
                  │   APPLIED    │
                  └──────────────┘
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## File Structure

```
gateai/scripts/
├── dedupe_resource_locks.py           ← Main arbiter script
├── test_dedupe_arbiter.py             ← Test suite
├── README_DEDUPE_ARBITER.md           ← User documentation
├── ARBITER_DELIVERY_SUMMARY.md        ← Delivery checklist
└── VISUAL_ARBITER_FLOW.md             ← This file (visual guide)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**KERNEL PHYSICAL ARBITER v1.0**  
**Visual Reference Guide**

