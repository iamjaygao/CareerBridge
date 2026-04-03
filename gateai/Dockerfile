FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install (requirements.txt lives at project root)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy only the gateai application source
COPY gateai/ /app/

# Environment
ENV DJANGO_SETTINGS_MODULE=gateai.settings_prod \
    PYTHONPATH=/app

# Collect static files, run migrations, then start server
CMD ["/bin/sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate --fake-initial && gunicorn gateai.wsgi:application --bind 0.0.0.0:8000 --workers 3"]

EXPOSE 8000
