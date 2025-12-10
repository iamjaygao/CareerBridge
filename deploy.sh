#!/bin/bash

# CareerBridge Production Deployment Script

set -e  # Exit on any error

echo "🚀 Starting CareerBridge Production Deployment..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please copy env.production.template to .env.production and configure your values."
    exit 1
fi

# Load environment variables
source .env.production

# Check required environment variables
required_vars=(
    "POSTGRES_PASSWORD"
    "SECRET_KEY"
    "ALLOWED_HOSTS"
    "JOB_CRAWLER_API_KEY"
    "RESUME_MATCHER_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set!"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p careerbridge/logs
mkdir -p careerbridge/media
mkdir -p nginx/ssl
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Generate SSL certificates (self-signed for development)
if [ ! -f nginx/ssl/cert.pem ]; then
    echo "🔐 Generating SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Create Nginx configuration
echo "🌐 Creating Nginx configuration..."
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream careerbridge {
        server careerbridge:8001;
    }
    
    upstream jobcrawler {
        server jobcrawler:8000;
    }
    
    upstream resumematcher {
        server resumematcher:8002;
    }

    server {
        listen 80;
        server_name localhost;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # CareerBridge API
        location /api/ {
            proxy_pass http://careerbridge;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # JobCrawler API
        location /jobcrawler/ {
            proxy_pass http://jobcrawler/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # ResumeMatcher API
        location /resumematcher/ {
            proxy_pass http://resumematcher/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Monitoring
        location /monitoring/ {
            proxy_pass http://grafana:3000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Create Prometheus configuration
echo "📊 Creating Prometheus configuration..."
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'careerbridge'
    static_configs:
      - targets: ['careerbridge:8001']
    metrics_path: '/metrics/'

  - job_name: 'jobcrawler'
    static_configs:
      - targets: ['jobcrawler:8000']
    metrics_path: '/metrics/'

  - job_name: 'resumematcher'
    static_configs:
      - targets: ['resumematcher:8002']
    metrics_path: '/metrics/'
EOF

# Create Grafana datasource configuration
echo "📈 Creating Grafana datasource configuration..."
mkdir -p monitoring/grafana/datasources
cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose -f docker-compose.prod.yml --env-file .env.production build

echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec careerbridge python manage.py migrate

# Create superuser if needed
echo "👤 Creating superuser..."
docker-compose -f docker-compose.prod.yml exec careerbridge python manage.py createsuperuser --noinput || true

# Collect static files
echo "📦 Collecting static files..."
docker-compose -f docker-compose.prod.yml exec careerbridge python manage.py collectstatic --noinput

# Health check
echo "🏥 Performing health checks..."
services=("careerbridge" "jobcrawler" "resumematcher")

for service in "${services[@]}"; do
    echo "Checking $service..."
    if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service health check failed"
    fi
done

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service URLs:"
echo "   CareerBridge API: https://localhost/api/"
echo "   JobCrawler API: https://localhost/jobcrawler/"
echo "   ResumeMatcher API: https://localhost/resumematcher/"
echo "   Monitoring: https://localhost/monitoring/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo "   Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "⚠️  Remember to:"
echo "   - Configure your domain in ALLOWED_HOSTS"
echo "   - Set up proper SSL certificates for production"
echo "   - Configure monitoring alerts"
echo "   - Set up backup strategies" 