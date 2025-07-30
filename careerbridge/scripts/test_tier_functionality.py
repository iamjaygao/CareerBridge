#!/usr/bin/env python3
"""
Test script for tier-based functionality
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
from resumes.models import Resume, UserSubscription, KeywordMatch
from resumes.tier_service import TierFactory, TierService

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

def test_subscription_management():
    """Test subscription management"""
    print("\n=== Testing Subscription Management ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get subscription info
    response = requests.get(f"{BASE_URL}/resumes/subscription/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User tier: {data['usage_stats']['tier']}")
        print(f"Uploads used: {data['usage_stats']['uploads_used']}/{data['usage_stats']['uploads_limit']}")
        print(f"Analyses used: {data['usage_stats']['analyses_used']}/{data['usage_stats']['analyses_limit']}")
        print(f"Matches used: {data['usage_stats']['matches_used']}/{data['usage_stats']['matches_limit']}")
    else:
        print(f"❌ Failed to get subscription: {response.text}")

def test_free_tier_keyword_matching():
    """Test free tier keyword matching"""
    print("\n=== Testing Free Tier Keyword Matching ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get user's resumes
    response = requests.get(f"{BASE_URL}/resumes/", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get resumes: {response.text}")
        return
    
    resumes = response.json()
    if not resumes:
        print("❌ No resumes found")
        return
    
    resume_id = resumes[0]['id']
    print(f"Using resume: {resumes[0]['title']}")
    
    # Test keyword matching
    keyword_data = {
        "resume_id": resume_id,
        "keywords": ["Python", "Django", "JavaScript", "React"],
        "job_title": "Software Engineer",
        "industry": "Technology"
    }
    
    response = requests.post(f"{BASE_URL}/resumes/keyword-match/", json=keyword_data, headers=headers)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Keyword match created with score: {result['keyword_match_score']}%")
        print(f"Matched keywords: {result['matched_keywords']}")
        print(f"Missing keywords: {result['missing_keywords']}")
        print(f"Recommendations: {len(result['basic_recommendations'])}")
    else:
        print(f"❌ Failed to create keyword match: {response.text}")

def test_premium_tier_jd_matching():
    """Test premium tier JD matching"""
    print("\n=== Testing Premium Tier JD Matching ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get user's resumes
    response = requests.get(f"{BASE_URL}/resumes/", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get resumes: {response.text}")
        return
    
    resumes = response.json()
    if not resumes:
        print("❌ No resumes found")
        return
    
    resume_id = resumes[0]['id']
    print(f"Using resume: {resumes[0]['title']}")
    
    # Test JD matching (this will fail for free tier users)
    jd_data = {
        "resume_id": resume_id,
        "jd_text": """
        We are looking for a Senior Software Engineer to join our team.
        
        Required Skills:
        - Python
        - JavaScript
        - SQL
        - Git
        
        Preferred Skills:
        - Django
        - React
        - AWS
        - Docker
        
        Experience: 3-7 years
        Education: Bachelor's degree in Computer Science or related field
        """,
        "job_title": "Senior Software Engineer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA"
    }
    
    response = requests.post(f"{BASE_URL}/resumes/premium-analysis/", json=jd_data, headers=headers)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ JD match created with score: {result['overall_match_score']}%")
        print(f"Match level: {result['match_level']}")
    elif response.status_code == 403:
        print("ℹ️ Expected: Premium tier required for JD matching")
    else:
        print(f"❌ Unexpected response: {response.text}")

def test_usage_limits():
    """Test usage limits"""
    print("\n=== Testing Usage Limits ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try to upload multiple resumes to test limits
    for i in range(5):
        resume_data = {
            "title": f"Test Resume {i+1}",
            "file": "dummy_file.pdf",  # This would be a real file in practice
            "file_size": 1024,
            "file_type": "pdf"
        }
        
        response = requests.post(f"{BASE_URL}/resumes/", json=resume_data, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Uploaded resume {i+1}")
        elif response.status_code == 403:
            print(f"ℹ️ Upload limit reached after {i} uploads")
            break
        else:
            print(f"❌ Failed to upload resume {i+1}: {response.text}")

def test_tier_upgrade():
    """Test tier upgrade functionality"""
    print("\n=== Testing Tier Upgrade ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try to upgrade to premium tier
    upgrade_data = {
        "tier": "premium"
    }
    
    response = requests.patch(f"{BASE_URL}/resumes/subscription/", json=upgrade_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Successfully upgraded to premium tier")
        
        # Test premium functionality
        test_premium_tier_jd_matching()
    else:
        print(f"❌ Failed to upgrade tier: {response.text}")

def test_enterprise_functionality():
    """Test enterprise functionality"""
    print("\n=== Testing Enterprise Functionality ===")
    
    # Login
    token = login_user("verified_user", "testpass123")
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test API config access
    response = requests.get(f"{BASE_URL}/resumes/api-configs/", headers=headers)
    
    if response.status_code == 200:
        print("✅ Enterprise API config access granted")
    elif response.status_code == 403:
        print("ℹ️ Expected: Enterprise tier required for API config access")
    else:
        print(f"❌ Unexpected response: {response.text}")
    
    # Test batch analysis
    batch_data = {
        "resume_ids": [1, 2],
        "jd_ids": [1, 2]
    }
    
    response = requests.post(f"{BASE_URL}/resumes/batch-analysis/", json=batch_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Enterprise batch analysis access granted")
    elif response.status_code == 403:
        print("ℹ️ Expected: Enterprise tier required for batch analysis")
    else:
        print(f"❌ Unexpected response: {response.text}")

def main():
    """Main test function"""
    print("🚀 Starting Tier Functionality Tests")
    
    # Test subscription management
    test_subscription_management()
    
    # Test free tier functionality
    test_free_tier_keyword_matching()
    
    # Test premium tier functionality
    test_premium_tier_jd_matching()
    
    # Test usage limits
    test_usage_limits()
    
    # Test tier upgrade
    test_tier_upgrade()
    
    # Test enterprise functionality
    test_enterprise_functionality()
    
    print("\n✅ All tier functionality tests completed!")

if __name__ == "__main__":
    main() 