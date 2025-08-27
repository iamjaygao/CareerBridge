FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Environment
ENV DJANGO_SETTINGS_MODULE=careerbridge.settings_prod \
    PYTHONPATH=/app

# Run migrations and start server
CMD ["/bin/sh", "-c", "python manage.py migrate && gunicorn careerbridge.wsgi:application --bind 0.0.0.0:8000 --workers 3"]

EXPOSE 8000
