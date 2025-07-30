#!/usr/bin/env python3
"""
Test script for resumes API
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_public_endpoints():
    """Test public endpoints (should return 401 for unauthenticated requests)"""
    print("Testing public endpoints (should require authentication)...")
    
    endpoints = [
        "/resumes/",
        "/resumes/1/",
        "/resumes/analyze/",
        "/resumes/stats/",
        "/resumes/templates/",
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url)
            print(f"GET {endpoint}: {response.status_code}")
            if response.status_code == 401:
                print("  ✓ Correctly requires authentication")
            else:
                print(f"  ⚠ Unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"GET {endpoint}: Connection failed (server not running)")
        except Exception as e:
            print(f"GET {endpoint}: Error - {e}")
    
    print()

def test_authentication():
    """Test user authentication"""
    print("Testing authentication...")
    
    # Test login
    login_data = {
        "login": "verified_user",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            print("  ✓ Login successful")
            return token
        else:
            print(f"  ❌ Login failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("  ❌ Connection failed (server not running)")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def test_resume_endpoints(token):
    """Test resume endpoints with authentication"""
    if not token:
        print("No token available, skipping authenticated tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("Testing authenticated resume endpoints...")
    
    # Test 1: Get resume list
    print("\n1. Testing GET /resumes/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} resumes")
            if data:
                print(f"  Sample resume: {data[0]['title']}")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 2: Get resume stats
    print("\n2. Testing GET /resumes/stats/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/stats/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Total resumes: {data['total_resumes']}")
            print(f"  ✓ Analyzed resumes: {data['analyzed_resumes']}")
            print(f"  ✓ Average score: {data['average_score']}")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 3: Get templates
    print("\n3. Testing GET /resumes/templates/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/templates/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} templates")
            if data:
                print(f"  Sample template: {data[0]['name']}")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 4: Search resumes
    print("\n4. Testing POST /resumes/search/")
    try:
        search_data = {
            "query": "Software Engineer"
        }
        response = requests.post(f"{BASE_URL}/resumes/search/", json=search_data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} matching resumes")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 5: Filter resumes
    print("\n5. Testing POST /resumes/filter/")
    try:
        filter_data = {
            "status": "analyzed"
        }
        response = requests.post(f"{BASE_URL}/resumes/filter/", json=filter_data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} analyzed resumes")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_analysis_endpoints(token):
    """Test analysis endpoints"""
    if not token:
        print("No token available, skipping analysis tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting analysis endpoints...")
    
    # Test 1: Get analysis for first resume
    print("\n1. Testing GET /resumes/analysis/1/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/analysis/1/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Overall score: {data['overall_score']}")
            print(f"  ✓ Score category: {data['score_category']}")
            print(f"  ✓ Technical skills: {len(data['technical_skills'])} found")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 2: Get feedback for first resume
    print("\n2. Testing GET /resumes/feedback/1/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/feedback/1/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Summary: {data['summary'][:100]}...")
            print(f"  ✓ Strengths: {len(data['strengths'])} found")
            print(f"  ✓ Weaknesses: {len(data['weaknesses'])} found")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_comparison_endpoints(token):
    """Test comparison endpoints"""
    if not token:
        print("No token available, skipping comparison tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting comparison endpoints...")
    
    # Test 1: Get comparisons
    print("\n1. Testing GET /resumes/comparisons/")
    try:
        response = requests.get(f"{BASE_URL}/resumes/comparisons/", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} comparisons")
        else:
            print(f"  ❌ Error: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("Testing Resumes API")
    print("=" * 60)
    
    # Test public endpoints
    test_public_endpoints()
    
    # Test authentication
    token = test_authentication()
    
    if token:
        # Test authenticated endpoints
        test_resume_endpoints(token)
        test_analysis_endpoints(token)
        test_comparison_endpoints(token)
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main() 