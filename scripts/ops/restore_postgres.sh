#!/usr/bin/env bash
# Restore a pg_dump -Fc archive into a database.
# Usage: scripts/ops/restore_postgres.sh <dump-file> [target-db]
#   target-db defaults to careerbridge_restore (a scratch copy). Restoring over
#   the live "careerbridge" database requires FORCE=1 and stopped app services.
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose -f docker-compose.prod.yml}"
DUMP="${1:?usage: restore_postgres.sh <dump-file> [target-db]}"
TARGET="${2:-careerbridge_restore}"

if [ "$TARGET" = "careerbridge" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "refusing to overwrite the live database without FORCE=1" >&2
  exit 2
fi

$COMPOSE exec -T postgres dropdb -U careerbridge_user --if-exists "$TARGET"
$COMPOSE exec -T postgres createdb -U careerbridge_user "$TARGET"
$COMPOSE exec -T postgres pg_restore -U careerbridge_user -d "$TARGET" --no-owner --exit-on-error < "$DUMP"
echo "restored $DUMP into $TARGET"
