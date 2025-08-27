#!/usr/bin/env python3
"""
External Services Integration Test Script

This script tests the integration with all external services including
AI services, third-party APIs, and communication services.
"""

import os
import sys
import django
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerbridge.settings')
django.setup()

from careerbridge.external_services.health_check import health_checker
from careerbridge.external_services.ai_services.openai_service import openai_service
from careerbridge.external_services.third_party_apis.email_service import email_service
from careerbridge.external_services.third_party_apis.job_crawler import job_crawler_service
from careerbridge.external_services.config import config


def test_configuration():
    """Test external service configurations"""
    print("🔧 Testing External Service Configurations...")
    print("=" * 50)
    
    # Test configuration validation
    validation_results = config.validate_config()
    service_status = config.get_service_status()
    
    print("Configuration Status:")
    for service, is_valid in validation_results.items():
        status = "✅ Configured" if is_valid else "❌ Not Configured"
        print(f"  {service}: {status}")
    
    print("\nService Status:")
    for service, status in service_status.items():
        print(f"  {service}: {status}")
    
    return validation_results


def test_health_check():
    """Test health check functionality"""
    print("\n🏥 Testing External Services Health Check...")
    print("=" * 50)
    
    try:
        health_report = health_checker.get_service_status_report()
        
        print(f"Overall Status: {health_report['health_check']['overall_status']}")
        print(f"Timestamp: {health_report['timestamp']}")
        
        print("\nService Health Details:")
        for service_name, result in health_report['health_check']['services'].items():
            status = result.get('status', 'unknown')
            status_icon = "✅" if status == "healthy" else "❌"
            print(f"  {status_icon} {service_name}: {status}")
            
            if result.get('error'):
                print(f"    Error: {result['error']}")
        
        print("\nSummary:")
        summary = health_report['health_check']['summary']
        print(f"  Total Services: {summary['total_services']}")
        print(f"  Healthy Services: {summary['healthy_services']}")
        print(f"  Unhealthy Services: {summary['unhealthy_services']}")
        print(f"  Health Percentage: {summary['health_percentage']:.1f}%")
        
        print("\nRecommendations:")
        for recommendation in health_report['recommendations']:
            print(f"  • {recommendation}")
        
        return health_report
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None


def test_openai_service():
    """Test OpenAI service functionality"""
    print("\n🤖 Testing OpenAI Service...")
    print("=" * 50)
    
    try:
        # Test health check
        health = openai_service.check_health()
        print(f"Health Status: {health.get('status')}")
        
        if health.get('status') == 'healthy':
            # Test resume analysis (with mock data)
            print("\nTesting Resume Analysis...")
            mock_resume = """
            John Doe
            Software Engineer
            
            Experience:
            - Senior Developer at Tech Corp (2020-2023)
            - Python, Django, React, AWS
            - Led team of 5 developers
            - Improved system performance by 40%
            """
            
            try:
                analysis = openai_service.analyze_resume(mock_resume)
                print("✅ Resume analysis completed")
                if analysis.get('parsed'):
                    print(f"  Overall Score: {analysis.get('overall_score', 'N/A')}")
                    print(f"  Strengths: {len(analysis.get('strengths', []))} items")
                    print(f"  Suggestions: {len(analysis.get('suggestions', []))} items")
                else:
                    print("  Analysis completed but not parsed as JSON")
            except Exception as e:
                print(f"❌ Resume analysis failed: {e}")
        
        return health
        
    except Exception as e:
        print(f"❌ OpenAI service test failed: {e}")
        return None


def test_email_service():
    """Test email service functionality"""
    print("\n📧 Testing Email Service...")
    print("=" * 50)
    
    try:
        # Test health check
        health = email_service.check_health()
        print(f"Health Status: {health.get('status')}")
        print(f"Provider: {health.get('provider', 'unknown')}")
        
        if health.get('status') == 'healthy':
            # Test email sending (with test data)
            print("\nTesting Email Sending...")
            test_data = {
                'user_name': 'Test User',
                'mentor_name': 'John Mentor',
                'appointment_date': '2024-01-15',
                'appointment_time': '10:00 AM',
                'appointment_type': 'Mock Interview'
            }
            
            try:
                # Note: This won't actually send an email in test mode
                result = email_service.send_notification_email(
                    to_email="test@example.com",
                    notification_type="appointment_confirmation",
                    data=test_data
                )
                print("✅ Email service test completed")
                print(f"  Result: {result}")
            except Exception as e:
                print(f"❌ Email sending test failed: {e}")
        
        return health
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return None


def test_job_crawler_service():
    """Test job crawler service functionality"""
    print("\n🔍 Testing Job Crawler Service...")
    print("=" * 50)
    
    try:
        # Test health check
        health = job_crawler_service.check_health()
        print(f"Health Status: {health.get('status')}")
        
        if health.get('status') == 'healthy':
            # Test job search (with mock data)
            print("\nTesting Job Search...")
            try:
                # This would make an actual API call if configured
                # For testing, we'll just check if the service is available
                print("✅ Job crawler service is available")
                print("  Note: Actual API calls require valid API key")
            except Exception as e:
                print(f"❌ Job search test failed: {e}")
        
        return health
        
    except Exception as e:
        print(f"❌ Job crawler service test failed: {e}")
        return None


def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report...")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'configuration': test_configuration(),
        'health_check': test_health_check(),
        'openai_service': test_openai_service(),
        'email_service': test_email_service(),
        'job_crawler_service': test_job_crawler_service()
    }
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    
    total_tests = 5
    passed_tests = 0
    
    if report['configuration']:
        config_valid = any(report['configuration'].values())
        if config_valid:
            passed_tests += 1
            print("✅ Configuration Test: PASSED")
        else:
            print("❌ Configuration Test: FAILED")
    
    if report['health_check']:
        health_status = report['health_check']['health_check']['overall_status']
        if health_status == 'healthy':
            passed_tests += 1
            print("✅ Health Check Test: PASSED")
        else:
            print("❌ Health Check Test: FAILED")
    
    if report['openai_service']:
        openai_status = report['openai_service'].get('status')
        if openai_status == 'healthy':
            passed_tests += 1
            print("✅ OpenAI Service Test: PASSED")
        else:
            print("❌ OpenAI Service Test: FAILED")
    
    if report['email_service']:
        email_status = report['email_service'].get('status')
        if email_status == 'healthy':
            passed_tests += 1
            print("✅ Email Service Test: PASSED")
        else:
            print("❌ Email Service Test: FAILED")
    
    if report['job_crawler_service']:
        crawler_status = report['job_crawler_service'].get('status')
        if crawler_status == 'healthy':
            passed_tests += 1
            print("✅ Job Crawler Service Test: PASSED")
        else:
            print("❌ Job Crawler Service Test: FAILED")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All external services are properly configured and healthy!")
    else:
        print("⚠️  Some services need configuration or are unhealthy.")
        print("Please check the recommendations above.")
    
    return report


def main():
    """Main test function"""
    print("🚀 CareerBridge External Services Integration Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        report = generate_test_report()
        
        # Save report to file
        report_file = f"external_services_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Test report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 