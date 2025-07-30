#!/usr/bin/env python3
"""
Simple test script for Mentors API
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"\n{'='*50}")
        print(f"Testing: {method} {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            try:
                result = response.json()
                if isinstance(result, list):
                    print(f"Items returned: {len(result)}")
                else:
                    print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print("❌ FAILED")
            print(f"Error: {response.text}")
        
        return response
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR: Cannot connect to {url}")
        return None
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🧪 Testing CareerBridge Mentors API")
    print("="*50)
    
    # Test 1: Basic connectivity
    print("\n1. Testing server connectivity...")
    response = test_endpoint("/mentors/")
    if not response:
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Test 2: Mentor listing
    print("\n2. Testing mentor listing...")
    test_endpoint("/mentors/")
    
    # Test 3: Mentor search
    print("\n3. Testing mentor search...")
    search_data = {
        "query": "technology",
        "service_type": "resume_review"
    }
    test_endpoint("/mentors/search/", method="POST", data=search_data)
    
    # Test 4: Mentor recommendations
    print("\n4. Testing mentor recommendations...")
    recommendation_data = {
        "service_type": "mock_interview",
        "limit": 5
    }
    test_endpoint("/mentors/recommendations/", method="POST", data=recommendation_data)
    
    # Test 5: Mentor rankings
    print("\n5. Testing mentor rankings...")
    ranking_data = {
        "ranking_type": "rating",
        "limit": 10
    }
    test_endpoint("/mentors/rankings/", method="POST", data=ranking_data)
    
    # Test 6: Mentor application (should fail without auth)
    print("\n6. Testing mentor application (should fail without auth)...")
    application_data = {
        "motivation": "I want to help students",
        "relevant_experience": "10+ years experience",
        "preferred_payment_method": "stripe"
    }
    test_endpoint("/mentors/apply/", method="POST", data=application_data)
    
    print("\n" + "="*50)
    print("🎉 Basic API Testing Complete!")
    print("\nTo see full API documentation, visit:")
    print("http://localhost:8000/swagger/")

if __name__ == "__main__":
    main() 