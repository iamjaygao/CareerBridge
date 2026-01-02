#!/usr/bin/env python3
"""
Script to reset user password
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def reset_user_password(username, new_password):
    """Reset password for a specific user"""
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"✅ Password reset successfully for user: {username}")
        print(f"   New password: {new_password}")
        return True
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")
        return False
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

def list_users():
    """List all users in the system"""
    users = User.objects.all()
    print("\n📋 All users in the system:")
    print("-" * 50)
    for user in users:
        print(f"Username: {user.username:<20} Email: {user.email:<30} Role: {user.role}")
    print("-" * 50)

def main():
    """Main function"""
    print("🔐 User Password Reset Tool")
    print("=" * 50)
    
    # List all users first
    list_users()
    
    # Get username from command line or prompt
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("\nEnter username to reset password: ").strip()
    
    if not username:
        print("❌ Username cannot be empty")
        return
    
    # Get new password
    if len(sys.argv) > 2:
        new_password = sys.argv[2]
    else:
        new_password = input("Enter new password: ").strip()
    
    if not new_password:
        print("❌ Password cannot be empty")
        return
    
    # Reset password
    reset_user_password(username, new_password)

if __name__ == '__main__':
    main() 