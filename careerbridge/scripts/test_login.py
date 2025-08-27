#!/usr/bin/env python3
"""
Script to test user login
"""

import os
import sys
import django
import requests
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

def test_login(username, password):
    """Test login with given credentials"""
    print(f"🔐 Testing login for user: {username}")
    print("=" * 50)
    
    # Method 1: Test with Django's authenticate function
    print("1. Testing with Django authenticate function:")
    user = authenticate(username=username, password=password)
    if user:
        print(f"   ✅ Login successful!")
        print(f"   User: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Is active: {user.is_active}")
        print(f"   Is staff: {user.is_staff}")
        print(f"   Is superuser: {user.is_superuser}")
    else:
        print(f"   ❌ Login failed!")
    
    print()
    
    # Method 2: Test with API endpoint
    print("2. Testing with API endpoint:")
    try:
        url = "http://localhost:8000/api/v1/users/login/"
        data = {
            "login": username,
            "password": password
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ API login successful!")
            print(f"   Access token: {result.get('access', 'N/A')[:20]}...")
            print(f"   User data: {result.get('user', {}).get('username', 'N/A')}")
        else:
            print(f"   ❌ API login failed!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Could not connect to API server. Make sure the server is running.")
    except Exception as e:
        print(f"   ❌ API test error: {e}")

def main():
    """Main function"""
    print("🔐 Login Test Tool")
    print("=" * 50)
    
    # Test with the current password
    username = "iamjaygao"
    password = "123456"
    
    test_login(username, password)
    
    # Also test with the old password
    print("\n" + "=" * 50)
    print("Testing with old password (newpassword123):")
    test_login(username, "newpassword123")

if __name__ == '__main__':
    main() 