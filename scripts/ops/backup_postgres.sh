#!/usr/bin/env bash
# Back up the production database to a custom-format dump (pg_dump -Fc).
# Usage: scripts/ops/backup_postgres.sh [output-file]
# Env:   COMPOSE (default: docker compose -f docker-compose.prod.yml)
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose -f docker-compose.prod.yml}"
OUT="${1:-backups/careerbridge-$(date -u +%Y%m%dT%H%M%SZ).dump}"
mkdir -p "$(dirname "$OUT")"

$COMPOSE exec -T postgres pg_dump -U careerbridge_user -d careerbridge --format=custom --no-owner > "$OUT"

# A dump that pg_restore cannot list is not a backup.
$COMPOSE exec -T postgres pg_restore --list < "$OUT" > /dev/null
echo "backup written: $OUT ($(wc -c < "$OUT") bytes)"
