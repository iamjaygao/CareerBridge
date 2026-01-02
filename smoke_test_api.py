#!/usr/bin/env python3
"""
Smoke test script for ResumeAuditEngine API endpoint.

Performs end-to-end HTTP smoke test for:
POST /api/engines/signal-core/resume-audit/

Usage:
    python smoke_test_api.py [--base-url BASE_URL] [--username USERNAME] [--password PASSWORD]

Requirements:
    - requests library
    - Valid user credentials (or create test user first)
"""

import sys
import json
import argparse
import requests
from typing import Dict, Any, Optional


def get_auth_token(base_url: str, username: str, password: str) -> Optional[str]:
    """
    Authenticate and get JWT token.
    
    Args:
        base_url: Base URL of the API
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        JWT token string or None if authentication fails
    """
    login_url = f"{base_url}/api/v1/users/login/"
    
    try:
        response = requests.post(
            login_url,
            json={
                'username': username,
                'password': password,
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access') or data.get('token')
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None


def create_test_user(base_url: str, username: str, password: str, email: str) -> bool:
    """
    Create a test user if it doesn't exist.
    
    Args:
        base_url: Base URL of the API
        username: Username for new user
        password: Password for new user
        email: Email for new user
        
    Returns:
        True if user created or already exists, False otherwise
    """
    register_url = f"{base_url}/api/v1/users/register/"
    
    try:
        response = requests.post(
            register_url,
            json={
                'username': username,
                'email': email,
                'password': password,
                'role': 'student',
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code in (200, 201):
            print(f"✓ Test user '{username}' created or already exists")
            return True
        elif response.status_code == 400:
            # User might already exist, try to login
            print(f"⚠ User might already exist, will try to login")
            return True
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User creation error: {str(e)}")
        return False


def run_smoke_test(base_url: str, token: str) -> bool:
    """
    Run smoke test for ResumeAuditEngine API.
    
    Args:
        base_url: Base URL of the API
        token: JWT authentication token
        
    Returns:
        True if all assertions pass, False otherwise
    """
    endpoint_url = f"{base_url}/api/engines/signal-core/resume-audit/"
    
    # Mock resume input
    decision_slot_id = "ds_smoke_test_001"
    resume_id = "resume_smoke_test_001"
    user_id = "user_smoke_test_001"
    
    resume_text = """
    John Doe
    Software Engineer
    
    Contact Information:
    Email: john.doe@example.com
    Phone: (555) 123-4567
    
    Professional Summary:
    Experienced software engineer with 5 years of expertise in Python, JavaScript, and React.
    Led development teams and delivered high-quality software solutions.
    
    Work Experience:
    
    Senior Software Engineer | Tech Corp Inc. | 2020 - Present
    - Led team of 10 developers in building scalable web applications
    - Increased system performance by 50% through optimization
    - Implemented CI/CD pipelines reducing deployment time by 40%
    - Technologies: Python, Django, React, PostgreSQL, AWS
    
    Software Engineer | StartupXYZ | 2018 - 2020
    - Developed RESTful APIs using Django and FastAPI
    - Built responsive frontend applications with React
    - Collaborated with cross-functional teams on product features
    - Technologies: Python, JavaScript, React, MongoDB
    
    Education:
    Bachelor of Science in Computer Science
    University of Technology | 2014 - 2018
    
    Skills:
    Technical: Python, JavaScript, React, Django, FastAPI, PostgreSQL, MongoDB, AWS, Docker, Git
    Soft Skills: Leadership, Communication, Problem Solving, Team Collaboration
    
    Certifications:
    - AWS Certified Developer Associate
    - Docker Certified Associate
    """
    
    request_payload = {
        "decision_slot_id": decision_slot_id,
        "resume_id": resume_id,
        "resume_text": resume_text.strip(),
        "user_id": user_id,
        "target_job_title": "Senior Software Engineer",
        "target_industry": "Technology",
        "target_keywords": ["Python", "React", "Leadership", "AWS"],
        "analysis_depth": "standard",
        "include_recommendations": True,
        "include_ats_compatibility": True,
    }
    
    print(f"\n🚀 Running smoke test for ResumeAuditEngine API")
    print(f"📍 Endpoint: {endpoint_url}")
    print(f"📋 Decision Slot ID: {decision_slot_id}")
    print(f"\n📤 Sending request...")
    
    try:
        response = requests.post(
            endpoint_url,
            json=request_payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            },
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        # Assertion 1: Status code should be 200
        if response.status_code != 200:
            print(f"❌ Assertion failed: Expected status_code 200, got {response.status_code}")
            print(f"Response body: {response.text}")
            return False
        
        print(f"✓ Assertion passed: response.status_code == 200")
        
        # Parse JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {str(e)}")
            print(f"Response text: {response.text}")
            return False
        
        # Pretty print response
        print(f"\n📄 Response JSON:")
        print(json.dumps(response_data, indent=2, default=str))
        
        # Assertion 2: Engine name
        if response_data.get("engine") != "ResumeAuditEngine":
            print(f"❌ Assertion failed: Expected engine 'ResumeAuditEngine', got '{response_data.get('engine')}'")
            return False
        
        print(f"✓ Assertion passed: response.json()['engine'] == 'ResumeAuditEngine'")
        
        # Assertion 3: Overall score is a number
        engine_output = response_data.get("engine_output", {})
        overall_score = engine_output.get("overall_score")
        
        if overall_score is None:
            print(f"❌ Assertion failed: 'engine_output.overall_score' is missing")
            return False
        
        if not isinstance(overall_score, (int, float)):
            print(f"❌ Assertion failed: 'engine_output.overall_score' is not a number, got {type(overall_score)}")
            return False
        
        print(f"✓ Assertion passed: response.json()['engine_output']['overall_score'] is a number ({overall_score})")
        
        # Assertion 4: Trace metadata exists and latency_ms is int
        trace = response_data.get("trace", {})
        
        if "latency_ms" not in trace:
            print(f"❌ Assertion failed: 'trace.latency_ms' is missing")
            return False
        
        latency_ms = trace.get("latency_ms")
        if not isinstance(latency_ms, int):
            print(f"❌ Assertion failed: 'trace.latency_ms' is not an int, got {type(latency_ms)}")
            return False
        
        print(f"✓ Assertion passed: response.json()['trace']['latency_ms'] exists and is int ({latency_ms})")
        
        # Additional validations
        if "contract_version" not in response_data:
            print(f"⚠ Warning: 'contract_version' is missing from response")
        else:
            print(f"✓ Contract version: {response_data['contract_version']}")
        
        if "decision_slot_id" not in engine_output:
            print(f"⚠ Warning: 'decision_slot_id' is missing from engine_output")
        else:
            if engine_output["decision_slot_id"] != decision_slot_id:
                print(f"⚠ Warning: decision_slot_id mismatch (expected {decision_slot_id}, got {engine_output['decision_slot_id']})")
            else:
                print(f"✓ Decision slot ID matches: {decision_slot_id}")
        
        if "signals" not in engine_output:
            print(f"⚠ Warning: 'signals' is missing from engine_output")
        else:
            signals_count = len(engine_output["signals"])
            print(f"✓ Signals generated: {signals_count}")
        
        print(f"\n✅ All assertions passed! Smoke test successful.")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for smoke test script."""
    parser = argparse.ArgumentParser(description='Smoke test for ResumeAuditEngine API')
    parser.add_argument(
        '--base-url',
        default='http://localhost:8001',
        help='Base URL of the API (default: http://localhost:8001)'
    )
    parser.add_argument(
        '--username',
        default='smoke_test_user',
        help='Username for authentication (default: smoke_test_user)'
    )
    parser.add_argument(
        '--password',
        default='smoke_test_pass123',
        help='Password for authentication (default: smoke_test_pass123)'
    )
    parser.add_argument(
        '--email',
        default='smoke_test@example.com',
        help='Email for test user creation (default: smoke_test@example.com)'
    )
    parser.add_argument(
        '--skip-auth',
        action='store_true',
        help='Skip authentication (requires valid token in --token)'
    )
    parser.add_argument(
        '--token',
        help='JWT token to use (if --skip-auth is set)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("ResumeAuditEngine API Smoke Test")
    print("=" * 70)
    print(f"Base URL: {args.base_url}")
    
    # Get authentication token
    token = None
    if args.skip_auth:
        if not args.token:
            print("❌ Error: --token is required when using --skip-auth")
            sys.exit(1)
        token = args.token
        print(f"✓ Using provided token (--skip-auth)")
    else:
        # Try to create test user first
        print(f"\n📝 Creating test user '{args.username}' if needed...")
        create_test_user(args.base_url, args.username, args.password, args.email)
        
        # Authenticate
        print(f"\n🔐 Authenticating as '{args.username}'...")
        token = get_auth_token(args.base_url, args.username, args.password)
        
        if not token:
            print("❌ Failed to get authentication token")
            print("\n💡 Tip: You can create a user manually or use --skip-auth with --token")
            sys.exit(1)
        
        print(f"✓ Authentication successful")
    
    # Run smoke test
    success = run_smoke_test(args.base_url, token)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Smoke test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Smoke test failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()

