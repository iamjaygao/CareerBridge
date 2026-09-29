#!/usr/bin/env bash
# Print "table rows md5" for every table in the public schema of a database.
# Two databases with identical output hold identical data.
# Usage: scripts/ops/db_fingerprint.sh [db]
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose -f docker-compose.prod.yml}"
DB="${1:-careerbridge}"

$COMPOSE exec -T postgres psql -U careerbridge_user -d "$DB" -At -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE t text; n bigint; h text;
BEGIN
  CREATE TEMP TABLE _fp(tbl text, rows bigint, md5 text);
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename LOOP
    EXECUTE format('SELECT count(*), coalesce(md5(string_agg(x::text, %L ORDER BY x::text)), %L) FROM %I x',
                   '|', 'empty', t) INTO n, h;
    INSERT INTO _fp VALUES (t, n, h);
  END LOOP;
END $$;
SELECT tbl || ' ' || rows || ' ' || md5 FROM _fp ORDER BY tbl;
SQL
