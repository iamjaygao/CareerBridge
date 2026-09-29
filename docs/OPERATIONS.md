# Operations runbook

## Health and monitoring

- `GET /health/` returns 200 with `"status": "healthy"` when the database and cache work, and 503 otherwise. No bus or feature flag can switch it off. nginx proxies it, and the Docker healthcheck uses it.
- `GET /metrics/` serves Prometheus metrics (django-prometheus, aggregated across gunicorn workers).
  - It is disabled unless `METRICS_TOKEN` is set, and it requires `Authorization: Bearer $METRICS_TOKEN`.
  - nginx does not route it; Prometheus scrapes `careerbridge:8000` directly.
  - Put the same token in `monitoring/metrics_token` (the file is not committed) for Prometheus.
- Grafana provisions the **CareerBridge overview** dashboard (uid `careerbridge-overview`) and the Prometheus datasource.
- Celery beat runs the schedule defined in `CELERY_BEAT_SCHEDULE`.
  - `kernel.tasks.beat_heartbeat` records its last run in the cache key `kernel:beat:last_heartbeat`. If that timestamp stops advancing, beat or the worker is down.
  - Periodic tasks of unlaunched modules do nothing while their bus is OFF.

## Postgres backups

Scripts are in `scripts/ops/`. They run against the compose stack and use `COMPOSE` (default `docker compose -f docker-compose.prod.yml`).

| Script | What it does |
|---|---|
| `backup_postgres.sh [file]` | `pg_dump --format=custom`, then checks the archive with `pg_restore --list` |
| `restore_postgres.sh <file> [db]` | Restores into `db` (default `careerbridge_restore`, a scratch copy). Overwriting the live `careerbridge` database needs `FORCE=1`, and the app, worker and beat must be stopped first |
| `db_fingerprint.sh [db]` | Prints `table rows md5` for every table; identical output means identical data |

### Schedule and retention

- **Daily** backup from the host's cron, for example `0 3 * * * cd /srv/careerbridge && scripts/ops/backup_postgres.sh`.
- Keep 7 daily and 4 weekly backups. Copy each dump **off the host**, to object storage with server-side encryption; a backup on the same disk is not a backup.
- Targets: RPO 24 h (one day of data at most), RTO 1 h.

### Restore test

- **Monthly**, and after every Postgres upgrade: restore the latest dump into `careerbridge_restore` and compare `db_fingerprint.sh` against the live database, taken right after the dump. CI does this on every push, in the `stack` job.
- Real recovery:
  1. `docker compose stop careerbridge celery_worker celery_beat`
  2. `FORCE=1 scripts/ops/restore_postgres.sh <dump> careerbridge`
  3. Start the services again, then check `/health/`.

## Required environment (production)

`SECRET_KEY` (freshly generated; never a value that has appeared in git history), `POSTGRES_PASSWORD`, `ALLOWED_HOSTS` (include `careerbridge` for the internal scrape), `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `METRICS_TOKEN`, `GRAFANA_PASSWORD`, and SMTP: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` (true/false), `DEFAULT_FROM_EMAIL`. Settings refuse to start when any of these is missing or malformed.
