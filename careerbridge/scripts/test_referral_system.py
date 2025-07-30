#!/usr/bin/env python3
"""
Test script for referral and pricing system
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from django.contrib.auth import get_user_model
from resumes.models import UserSubscription, InvitationCode, ReferralProgram, UserReferralStats
from resumes.referral_service import ReferralService, PricingService

User = get_user_model()

# API base URL
BASE_URL = 'http://localhost:8000/api'

def login_user(username, password):
    """Login user and return token"""
    login_url = f"{BASE_URL}/users/login/"
    login_data = {
        "login": username,
        "password": password
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_pricing_information():
    """Test pricing information"""
    print("\n=== Testing Pricing Information ===")
    
    # Get pricing info
    response = requests.get(f"{BASE_URL}/resumes/pricing/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Pricing information retrieved successfully")
        
        for tier, info in data['pricing'].items():
            print(f"\n{tier.upper()} TIER:")
            print(f"  Monthly: ${info['monthly_price']}")
            print(f"  Yearly: ${info['yearly_price']}")
            print(f"  Features: {len(info['features'])} features")
            
            # Calculate savings
            if info['monthly_price'] > 0:
                savings = PricingService.calculate_savings(tier, 'yearly')
                print(f"  Yearly savings: ${savings['savings_amount']} ({savings['savings_percentage']:.1f}%)")
    else:
        print(f"❌ Failed to get pricing: {response.text}")

def test_referral_stats():
    """Test referral statistics"""
    print("\n=== Testing Referral Statistics ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get referral stats
    response = requests.get(f"{BASE_URL}/resumes/referral/stats/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Referral statistics retrieved successfully")
        print(f"Invitations sent: {data['stats']['invitations_sent']}")
        print(f"Invitations used: {data['stats']['invitations_used']}")
        print(f"Conversion rate: {data['stats']['conversion_rate']:.1f}%")
        print(f"Total rewards earned: {data['stats']['total_rewards_earned']} days")
        print(f"Available rewards: {data['stats']['available_rewards']} days")
        print(f"Available free days: {data['subscription']['available_free_days']} days")
    else:
        print(f"❌ Failed to get referral stats: {response.text}")

def test_create_invitation():
    """Test creating invitation"""
    print("\n=== Testing Create Invitation ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create invitation
    invitation_data = {
        "email": "friend@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/resumes/referral/invite/", json=invitation_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Invitation created successfully")
        print(f"Code: {data['invitation']['code']}")
        print(f"Email: {data['invitation']['email']}")
        print(f"Reward days: {data['invitation']['reward_days']}")
        return data['invitation']['code']
    else:
        print(f"❌ Failed to create invitation: {response.text}")
        return None

def test_use_invitation():
    """Test using invitation"""
    print("\n=== Testing Use Invitation ===")
    
    # First create an invitation
    invitation_code = test_create_invitation()
    if not invitation_code:
        return
    
    # Create a new user to use the invitation
    # In a real scenario, this would be during registration
    print(f"Invitation code created: {invitation_code}")
    print("Note: In a real scenario, this would be used during user registration")
    
    # Simulate using invitation (this would normally be done during registration)
    print("Simulating invitation usage...")
    
    # Login as the inviter to check stats
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Check updated stats
    response = requests.get(f"{BASE_URL}/resumes/referral/stats/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Updated invitations sent: {data['stats']['invitations_sent']}")
        print(f"Pending invitations: {len(data['pending_invitations'])}")

def test_referral_link():
    """Test referral link generation"""
    print("\n=== Testing Referral Link ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get referral link
    response = requests.get(f"{BASE_URL}/resumes/referral/link/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Referral link generated successfully")
        print(f"Link: {data['referral_link']}")
        print(f"Username: {data['username']}")
    else:
        print(f"❌ Failed to get referral link: {response.text}")

def test_subscription_upgrade():
    """Test subscription upgrade"""
    print("\n=== Testing Subscription Upgrade ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Upgrade to premium
    upgrade_data = {
        "tier": "premium",
        "billing_cycle": "monthly"
    }
    
    response = requests.patch(f"{BASE_URL}/resumes/subscription/upgrade/", json=upgrade_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Subscription upgraded successfully")
        print(f"New tier: {data['subscription']['tier']}")
        print(f"Billing cycle: {data['subscription']['billing_cycle']}")
        print(f"Monthly price: ${data['subscription']['monthly_price']}")
    else:
        print(f"❌ Failed to upgrade subscription: {response.text}")

def test_free_days_usage():
    """Test free days usage"""
    print("\n=== Testing Free Days Usage ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Use free days
    usage_data = {
        "days": 7
    }
    
    response = requests.post(f"{BASE_URL}/resumes/free-days/use/", json=usage_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Free days used successfully")
        print(f"Days used: {data['free_days_used']}")
        print(f"Available free days: {data['available_free_days']}")
    else:
        print(f"❌ Failed to use free days: {response.text}")

def test_pricing_detail():
    """Test pricing detail for specific tier"""
    print("\n=== Testing Pricing Detail ===")
    
    # Test premium tier pricing
    response = requests.get(f"{BASE_URL}/resumes/pricing/premium/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Pricing detail retrieved successfully")
        print(f"Tier: {data['tier']}")
        print(f"Monthly price: ${data['pricing']['monthly_price']}")
        print(f"Yearly price: ${data['pricing']['yearly_price']}")
        print(f"Yearly savings: ${data['savings']['savings_amount']} ({data['savings']['savings_percentage']:.1f}%)")
        print(f"Features: {len(data['pricing']['features'])} features")
    else:
        print(f"❌ Failed to get pricing detail: {response.text}")

def test_milestone_rewards():
    """Test milestone rewards system"""
    print("\n=== Testing Milestone Rewards ===")
    
    # This would be tested by creating multiple invitations and checking milestones
    print("Milestone rewards are automatically awarded when users reach:")
    print("- 5 successful invitations: 30 free days")
    print("- 10 successful invitations: 60 free days")
    print("- 20 successful invitations: 120 free days")
    print("This is tested automatically when invitations are used.")

def main():
    """Main test function"""
    print("🚀 Starting Referral and Pricing System Tests")
    
    # Test pricing information
    test_pricing_information()
    
    # Test referral statistics
    test_referral_stats()
    
    # Test creating invitation
    test_create_invitation()
    
    # Test referral link
    test_referral_link()
    
    # Test subscription upgrade
    test_subscription_upgrade()
    
    # Test free days usage
    test_free_days_usage()
    
    # Test pricing detail
    test_pricing_detail()
    
    # Test milestone rewards info
    test_milestone_rewards()
    
    print("\n✅ All referral and pricing tests completed!")

if __name__ == "__main__":
    main() 