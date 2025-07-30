# CareerBridge Production Deployment Guide

This guide covers the complete production deployment process for CareerBridge.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Static Files Configuration](#static-files-configuration)
6. [Web Server Configuration](#web-server-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Deployment Scripts](#deployment-scripts)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL (recommended) or SQLite
- Redis (optional, for caching)
- Nginx or Apache web server
- SSL certificate

### Python Dependencies
Install production dependencies:
```bash
pip install -r requirements_prod.txt
```

## Environment Setup

### 1. Environment Variables
Create a `.env` file in the project root:
```bash
cp env_template.txt .env
```

Then update the `.env` file with your actual values:

```env
# Django Settings
DJANGO_ENV=production
DJANGO_SECRET_KEY=your-secure-secret-key

# Database Settings
DB_ENGINE=postgresql  # or sqlite
DB_NAME=careerbridge
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Settings (optional)
REDIS_URL=redis://127.0.0.1:6379/1

# External API Settings
JOB_CRAWLER_API_URL=https://your-job-crawler-api.com
RESUME_MATCHER_API_URL=https://your-resume-matcher-api.com
AI_ANALYSIS_API_URL=https://your-ai-analysis-api.com

# Security Settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

### 2. Load Environment Variables
```bash
export $(cat .env | xargs)
```

## Database Configuration

### PostgreSQL (Recommended)
1. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. Create database and user:
```sql
CREATE DATABASE careerbridge;
CREATE USER careerbridge_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE careerbridge TO careerbridge_user;
```

3. Update `.env` file with PostgreSQL settings.

### SQLite (Development/Testing)
For development or testing, SQLite is used by default. No additional configuration needed.

## Security Configuration

### 1. Secret Key
Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Security Headers
The production settings include:
- HTTPS redirect
- HSTS (HTTP Strict Transport Security)
- Secure cookies
- XSS protection
- Content type sniffing protection
- Frame options

### 3. Allowed Hosts
Update `ALLOWED_HOSTS` in your `.env` file with your actual domain names.

## Static Files Configuration

### 1. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 2. Configure Web Server
Static files are served from the `staticfiles` directory.

## Web Server Configuration

### Nginx Configuration
Create `/etc/nginx/sites-available/careerbridge`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static Files
    location /static/ {
        alias /path/to/careerbridge/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /path/to/careerbridge/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/careerbridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/HTTPS Setup

### Let's Encrypt (Recommended)
1. Install Certbot:
```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtain certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. Auto-renewal:
```bash
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### 1. Log Files
Logs are stored in the `logs` directory:
- `django.log` - Django application logs
- `gunicorn_access.log` - Gunicorn access logs
- `gunicorn_error.log` - Gunicorn error logs

### 2. Log Rotation
Configure log rotation in `/etc/logrotate.d/careerbridge`:

```
/path/to/careerbridge/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload gunicorn
    endscript
}
```

### 3. Monitoring
Consider setting up:
- Sentry for error tracking
- Prometheus/Grafana for metrics
- Uptime monitoring

## Deployment Scripts

### Automated Deployment
Use the provided deployment script:
```bash
python deploy.py
```

This script will:
1. Check prerequisites
2. Install dependencies
3. Run migrations
4. Collect static files
5. Run security checks
6. Run tests
7. Create superuser (if needed)

### Manual Deployment Steps
If you prefer manual deployment:

1. **Install dependencies:**
```bash
pip install -r requirements_prod.txt
```

2. **Run migrations:**
```bash
python manage.py migrate
```

3. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

4. **Create superuser:**
```bash
python manage.py createsuperuser
```

5. **Start Gunicorn:**
```bash
gunicorn careerbridge.wsgi:application -c gunicorn.conf.py
```

### Systemd Service
Create `/etc/systemd/system/careerbridge.service`:

```ini
[Unit]
Description=CareerBridge Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/careerbridge
Environment="PATH=/path/to/venv/bin"
Environment="DJANGO_ENV=production"
ExecStart=/path/to/venv/bin/gunicorn --config gunicorn.conf.py careerbridge.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable careerbridge
sudo systemctl start careerbridge
```

## Troubleshooting

### Common Issues

1. **Permission Errors:**
```bash
sudo chown -R www-data:www-data /path/to/careerbridge
sudo chmod -R 755 /path/to/careerbridge
```

2. **Database Connection Issues:**
- Check database credentials in `.env`
- Ensure database server is running
- Verify network connectivity

3. **Static Files Not Loading:**
- Run `python manage.py collectstatic`
- Check nginx configuration
- Verify file permissions

4. **SSL Certificate Issues:**
- Check certificate expiration
- Verify domain configuration
- Test with `openssl s_client`

### Debug Mode
For troubleshooting, temporarily enable debug mode:
```bash
export DJANGO_ENV=development
```

### Log Analysis
Check logs for errors:
```bash
tail -f logs/django.log
tail -f logs/gunicorn_error.log
```

## Performance Optimization

### 1. Database Optimization
- Use database indexes
- Optimize queries
- Consider read replicas for high traffic

### 2. Caching
- Enable Redis caching
- Use Django's cache framework
- Implement CDN for static files

### 3. Gunicorn Tuning
Adjust worker processes in `gunicorn.conf.py`:
```python
workers = multiprocessing.cpu_count() * 2 + 1
```

## Backup Strategy

### 1. Database Backups
```bash
# PostgreSQL
pg_dump careerbridge > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

### 2. Media Files
```bash
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

### 3. Automated Backups
Set up cron jobs for automated backups:
```bash
# Daily database backup
0 2 * * * /path/to/backup_script.sh
```

## Security Checklist

- [ ] HTTPS enabled
- [ ] Secure secret key
- [ ] Debug mode disabled
- [ ] Allowed hosts configured
- [ ] Security headers set
- [ ] Database credentials secure
- [ ] File permissions correct
- [ ] Logs monitored
- [ ] Regular backups
- [ ] SSL certificate valid
- [ ] Dependencies updated
- [ ] Security patches applied

## Support

For deployment issues:
1. Check the logs in `logs/` directory
2. Verify environment variables
3. Test with development settings
4. Review this documentation
5. Check Django deployment checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/ 