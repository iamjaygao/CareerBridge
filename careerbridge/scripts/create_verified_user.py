#!/usr/bin/env python3
"""
Script to create a verified test user for API testing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_verified_user():
    """Create a verified test user"""
    username = 'verified_user'
    email = 'verified@example.com'
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"User {username} already exists")
    else:
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            first_name='Verified',
            last_name='User',
            role='student'
        )
        print(f"Created user: {username}")
    
    # Verify email
    user.email_verified = True
    user.email_verification_sent_at = None
    user.save()
    
    print(f"Email verified for user: {username}")
    print(f"Login credentials:")
    print(f"  Username: {username}")
    print(f"  Password: testpass123")
    print(f"  Email: {email}")
    
    return user

if __name__ == '__main__':
    create_verified_user() 