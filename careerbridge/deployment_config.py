"""
Deployment configuration for CareerBridge.

This file contains helper functions and configurations for production deployment.
"""

import os
import secrets
from pathlib import Path


def generate_secret_key():
    """Generate a secure secret key for Django."""
    return secrets.token_urlsafe(50)


def create_env_file():
    """Create a .env file template for production deployment."""
    env_content = """# Django Settings
DJANGO_ENV=production
DJANGO_SECRET_KEY={secret_key}

# Database Settings
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

# Redis Settings
REDIS_URL=redis://127.0.0.1:6379/1

# External API Settings
JOB_CRAWLER_API_URL=https://your-job-crawler-api.com
RESUME_MATCHER_API_URL=https://your-resume-matcher-api.com
AI_ANALYSIS_API_URL=https://your-ai-analysis-api.com

# Security Settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
""".format(secret_key=generate_secret_key())
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("Created .env file with template values. Please update with your actual values.")


def check_production_requirements():
    """Check if all production requirements are met."""
    requirements = [
        ('DJANGO_SECRET_KEY', 'Secret key must be set'),
        ('DB_PASSWORD', 'Database password must be set'),
        ('EMAIL_HOST_PASSWORD', 'Email password must be set'),
        ('ALLOWED_HOSTS', 'Allowed hosts must be configured'),
    ]
    
    missing = []
    for var, description in requirements:
        if not os.environ.get(var):
            missing.append(f"{var}: {description}")
    
    if missing:
        print("Missing required environment variables:")
        for item in missing:
            print(f"  - {item}")
        return False
    
    print("All production requirements are met.")
    return True


def setup_production_directories():
    """Create necessary directories for production."""
    directories = [
        'logs',
        'staticfiles',
        'media',
        'backups',
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")


if __name__ == "__main__":
    print("CareerBridge Deployment Configuration")
    print("=" * 40)
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_env_file()
    
    # Setup directories
    setup_production_directories()
    
    # Check requirements
    check_production_requirements() 