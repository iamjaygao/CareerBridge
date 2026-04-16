# ── Stage 1: Build ────────────────────────────────────────────────────────────
# Install C-compiled deps (psycopg2, etc.) then discard build toolchain.
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=gateai.settings_prod \
    PYTHONPATH=/app

# Only runtime system libs (no gcc/make)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin

WORKDIR /app

# Copy application source
COPY gateai/ /app/

# Non-root user — security best practice
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser && \
    mkdir -p /app/media /app/logs /app/staticfiles && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Gunicorn workers scale with CPU: default 2×cores+1, override via GUNICORN_WORKERS.
# Timeout 120s covers OpenAI/Stripe API calls.
# migrate (no --fake-initial) is safe: Django migration lock prevents races.
CMD ["/bin/sh", "-c", \
    "python manage.py collectstatic --noinput && \
     python manage.py migrate && \
     gunicorn gateai.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers ${GUNICORN_WORKERS:-3} \
       --timeout ${GUNICORN_TIMEOUT:-120} \
       --access-logfile -"]
