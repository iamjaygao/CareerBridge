# Database Reset Steps - Local Dev Only

## ✅ COMPLETED

### STEP 1 — Migration Files Purged
All migration `.py` files have been deleted (except `__init__.py` files).
- Command executed: `find . -path "*/migrations/*.py" -not -name "__init__.py" -delete`
- Verification: 0 migration files remaining

## ⚠️ REMAINING STEPS (Require Full System Access)

Due to sandbox restrictions, the following steps need to be run manually with full system access:

### STEP 0 — Backup Accounts (if not done)
```bash
cd gateai
python3 manage.py dumpdata auth.user --indent 4 > users_backup.json
```

### STEP 2 — Reset PostgreSQL Schema
```bash
cd gateai
python3 manage.py dbshell
```

Inside psql, run:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
\q
```

### STEP 3 — Rebuild Kernel Database
```bash
cd gateai
python3 manage.py makemigrations
python3 manage.py migrate
```

### STEP 4 — Restore Accounts
```bash
cd gateai
python3 manage.py loaddata users_backup.json
```

### STEP 5 — Final Verification
```bash
cd gateai
python3 manage.py check
```

Expected output: "System check identified no issues (0 silenced)."

## Notes
- Migration files have been successfully purged
- Database reset requires direct database access (not available in sandbox)
- All user accounts will be preserved via backup/restore process

