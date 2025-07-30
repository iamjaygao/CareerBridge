#!/usr/bin/env python3
"""
CareerBridge Project Initialization Script
This script sets up the project for first-time use.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Setup Django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def run_command(command, description):
    """Run a management command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    try:
        execute_from_command_line(command)
        print(f"✅ {description} completed successfully")
        return True
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def create_superuser():
    """Create a superuser if none exists"""
    if User.objects.filter(is_superuser=True).exists():
        print("✅ Superuser already exists")
        return True
    
    print("\n" + "="*50)
    print("Creating superuser...")
    print("="*50)
    
    try:
        # Create superuser with default credentials
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@careerbridge.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print(f"✅ Superuser created: {superuser.username}")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@careerbridge.com")
        return True
    except Exception as e:
        print(f"❌ Failed to create superuser: {e}")
        return False

def check_database():
    """Check if database is properly set up"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 CareerBridge Project Initialization")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path('manage.py').exists():
        print("❌ Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Step 1: Check database connection
    if not check_database():
        print("❌ Database connection failed. Please check your database settings.")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_command(['manage.py', 'makemigrations'], "Creating migrations"):
        print("❌ Migration creation failed")
        sys.exit(1)
    
    if not run_command(['manage.py', 'migrate'], "Applying migrations"):
        print("❌ Migration application failed")
        sys.exit(1)
    
    # Step 3: Collect static files
    if not run_command(['manage.py', 'collectstatic', '--noinput'], "Collecting static files"):
        print("⚠️  Static file collection failed (this might be okay in development)")
    
    # Step 4: Create superuser
    if not create_superuser():
        print("❌ Superuser creation failed")
        sys.exit(1)
    
    # Step 5: Create test data
    print("\n" + "="*50)
    print("Creating test data...")
    print("="*50)
    
    try:
        # Import and run test data creation
        from scripts.create_test_data import main as create_test_data
        create_test_data()
        print("✅ Test data created successfully")
    except Exception as e:
        print(f"⚠️  Test data creation failed: {e}")
        print("   You can run it manually later with: python scripts/create_test_data.py")
    
    # Step 6: Create initial system configuration
    print("\n" + "="*50)
    print("Setting up initial system configuration...")
    print("="*50)
    
    try:
        from adminpanel.models import SystemConfig
        
        # Create default system configurations
        default_configs = [
            {
                'key': 'site_name',
                'value': 'CareerBridge',
                'config_type': 'general',
                'description': 'Site name displayed throughout the application'
            },
            {
                'key': 'site_description',
                'value': 'Professional career development platform connecting mentors and students',
                'config_type': 'general',
                'description': 'Site description for SEO and display purposes'
            },
            {
                'key': 'default_currency',
                'value': 'USD',
                'config_type': 'payment',
                'description': 'Default currency for payments and pricing'
            },
            {
                'key': 'platform_fee_percentage',
                'value': '15',
                'config_type': 'payment',
                'description': 'Platform fee percentage for mentor sessions'
            },
            {
                'key': 'max_file_size_mb',
                'value': '10',
                'config_type': 'general',
                'description': 'Maximum file size for resume uploads in MB'
            },
            {
                'key': 'email_notifications_enabled',
                'value': 'true',
                'config_type': 'notification',
                'description': 'Enable email notifications globally'
            }
        ]
        
        for config_data in default_configs:
            config, created = SystemConfig.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )
            if created:
                print(f"✅ Created config: {config.key}")
            else:
                print(f"ℹ️  Config already exists: {config.key}")
        
        print("✅ System configuration setup completed")
        
    except Exception as e:
        print(f"⚠️  System configuration setup failed: {e}")
    
    # Final success message
    print("\n" + "🎉" + "="*48 + "🎉")
    print("🎉 CareerBridge Project Initialization Complete! 🎉")
    print("="*50)
    print("\n📋 Next Steps:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Access the admin interface:")
    print("   http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n3. Access the API documentation:")
    print("   http://127.0.0.1:8000/swagger/")
    print("\n4. Test the API endpoints:")
    print("   http://127.0.0.1:8000/api/")
    print("\n📚 Documentation:")
    print("- README.md: Project overview and setup")
    print("- DEPLOYMENT.md: Deployment instructions")
    print("- scripts/README.md: Available scripts")
    print("\n🔧 Development:")
    print("- Run tests: python manage.py test")
    print("- Create more test data: python scripts/create_test_data.py")
    print("- Check code quality: python manage.py check")
    print("\n" + "="*50)

if __name__ == '__main__':
    main() 