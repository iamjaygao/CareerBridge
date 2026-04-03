#!/bin/bash

# CareerBridge Production Deployment Script

set -e  # Exit on any error

echo "Starting CareerBridge Production Deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy env.production.template to .env and configure your values."
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
required_vars=(
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
    "ALLOWED_HOSTS"
    "CORS_ALLOWED_ORIGINS"
    "CSRF_TRUSTED_ORIGINS"
    "JOB_CRAWLER_API_KEY"
    "RESUME_MATCHER_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set!"
        exit 1
    fi
done

echo "Environment variables validated"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p gateai/logs
mkdir -p gateai/media
mkdir -p nginx/ssl
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Generate self-signed SSL certificate if not present
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/C=US/ST=State/L=City/O=CareerBridge/CN=localhost"
fi

# Build frontend
echo "Building frontend..."
cd frontend && npm ci && npm run build && cd ..

# Build and start services
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml --env-file .env build

echo "Starting services..."
docker compose -f docker-compose.prod.yml --env-file .env up -d

# Wait for careerbridge to be healthy (max 60s)
echo "Waiting for careerbridge to be healthy..."
for i in $(seq 1 12); do
    if docker compose -f docker-compose.prod.yml exec -T careerbridge curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
        echo "careerbridge is healthy"
        break
    fi
    if [ "$i" -eq 12 ]; then
        echo "Timeout: careerbridge did not become healthy in 60s"
        docker compose -f docker-compose.prod.yml logs careerbridge
        exit 1
    fi
    sleep 5
done

echo "Deployment completed successfully!"
echo ""
echo "Service URLs:"
echo "   CareerBridge: http://localhost/"
echo "   API:          http://localhost/api/"
echo "   Admin:        http://localhost/admin/"
echo "   Grafana:      http://127.0.0.1:3000/"
echo "   Prometheus:   http://127.0.0.1:9090/"
echo ""
echo "Useful commands:"
echo "   Logs:    docker compose -f docker-compose.prod.yml logs -f"
echo "   Stop:    docker compose -f docker-compose.prod.yml down"
echo "   Restart: docker compose -f docker-compose.prod.yml restart"
