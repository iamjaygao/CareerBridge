#!/usr/bin/env python3
"""
Production deployment script for CareerBridge.

This script automates the deployment process for production environments.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠ Warning: Virtual environment not detected")
    
    print("✓ Prerequisites check completed")
    return True


def install_dependencies():
    """Install production dependencies."""
    return run_command(
        "pip install -r requirements_prod.txt",
        "Installing production dependencies"
    )


def run_migrations():
    """Run database migrations."""
    return run_command(
        "python manage.py migrate",
        "Running database migrations"
    )


def collect_static_files():
    """Collect static files for production."""
    return run_command(
        "python manage.py collectstatic --noinput",
        "Collecting static files"
    )


def run_security_checks():
    """Run Django security checks."""
    return run_command(
        "python manage.py check --deploy",
        "Running security checks"
    )


def run_tests():
    """Run all tests to ensure everything works."""
    return run_command(
        "python manage.py test",
        "Running tests"
    )


def create_superuser():
    """Create a superuser if none exists."""
    print("\nChecking for superuser...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            print("No superuser found. Creating one...")
            return run_command(
                "python manage.py createsuperuser --noinput",
                "Creating superuser"
            )
        else:
            print("✓ Superuser already exists")
            return True
    except Exception as e:
        print(f"✗ Error checking superuser: {e}")
        return False


def setup_logging():
    """Setup logging directories."""
    print("\nSetting up logging...")
    
    log_dirs = ['logs', 'staticfiles', 'media', 'backups']
    for log_dir in log_dirs:
        Path(log_dir).mkdir(exist_ok=True)
        print(f"✓ Created directory: {log_dir}")
    
    return True


def main():
    """Main deployment function."""
    print("CareerBridge Production Deployment")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("✗ Error: manage.py not found. Please run this script from the Django project root.")
        sys.exit(1)
    
    # Set production environment
    os.environ['DJANGO_ENV'] = 'production'
    
    steps = [
        ("Prerequisites check", check_prerequisites),
        ("Setup logging", setup_logging),
        ("Install dependencies", install_dependencies),
        ("Run migrations", run_migrations),
        ("Collect static files", collect_static_files),
        ("Run security checks", run_security_checks),
        ("Run tests", run_tests),
        ("Create superuser", create_superuser),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n✗ Deployment failed. Failed steps: {', '.join(failed_steps)}")
        sys.exit(1)
    else:
        print(f"\n✓ Deployment completed successfully!")
        print("\nNext steps:")
        print("1. Configure your web server (nginx/apache)")
        print("2. Set up SSL certificates")
        print("3. Configure environment variables in .env file")
        print("4. Start the application with: gunicorn careerbridge.wsgi:application")


if __name__ == "__main__":
    main() 