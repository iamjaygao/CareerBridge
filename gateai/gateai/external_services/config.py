"""
External Services Configuration

This module contains configuration settings for all external services
including AI services, third-party APIs, and communication services.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str
    model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class EmailConfig:
    """Email service configuration"""
    provider: str = "sendgrid"  # sendgrid, ses, smtp
    api_key: Optional[str] = None
    from_email: str = "noreply@careerbridge.com"
    from_name: str = "CareerBridge"
    template_id: Optional[str] = None


@dataclass
class SMSConfig:
    """SMS service configuration"""
    provider: str = "twilio"  # twilio, aws_sns
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    from_number: Optional[str] = None


@dataclass
class JobCrawlerConfig:
    """Job crawler API configuration"""
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8000"  # Independent Job Crawler service
    timeout: int = 30
    rate_limit: int = 100  # requests per hour


@dataclass
class ResumeMatcherConfig:
    """Resume matching API configuration"""
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8002"
    timeout: int = 30
    confidence_threshold: float = 0.7


class ExternalServicesConfig:
    """Main configuration class for all external services"""
    
    def __init__(self):
        self.openai = OpenAIConfig(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
            timeout=int(os.getenv('OPENAI_TIMEOUT', '30'))
        )
        
        self.email = EmailConfig(
            provider=os.getenv('EMAIL_PROVIDER', 'sendgrid'),
            api_key=os.getenv('EMAIL_API_KEY'),
            from_email=os.getenv('EMAIL_FROM', 'noreply@careerbridge.com'),
            from_name=os.getenv('EMAIL_FROM_NAME', 'CareerBridge'),
            template_id=os.getenv('EMAIL_TEMPLATE_ID')
        )
        
        self.sms = SMSConfig(
            provider=os.getenv('SMS_PROVIDER', 'twilio'),
            account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
            auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
            from_number=os.getenv('TWILIO_FROM_NUMBER')
        )
        
        self.job_crawler = JobCrawlerConfig(
            api_key=os.getenv('JOB_CRAWLER_API_KEY', 'dev-api-key'),
            base_url=os.getenv('JOB_CRAWLER_BASE_URL', 'http://localhost:8000'),
            timeout=int(os.getenv('JOB_CRAWLER_TIMEOUT', '30')),
            rate_limit=int(os.getenv('JOB_CRAWLER_RATE_LIMIT', '100'))
        )
        
        self.resume_matcher = ResumeMatcherConfig(
            api_key=os.getenv('RESUME_MATCHER_API_KEY', 'dev-api-key'),
            base_url=os.getenv('RESUME_MATCHER_BASE_URL', 'http://localhost:8002'),
            timeout=int(os.getenv('RESUME_MATCHER_TIMEOUT', '30')),
            confidence_threshold=float(os.getenv('RESUME_MATCHER_CONFIDENCE', '0.7'))
        )
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate all external service configurations"""
        validation_results = {
            'openai': bool(self.openai.api_key),
            'email': bool(self.email.api_key),
            'sms': bool(self.sms.account_sid and self.sms.auth_token),
            'job_crawler': bool(self.job_crawler.api_key),
            'resume_matcher': bool(self.resume_matcher.api_key)
        }
        return validation_results
    
    def get_service_status(self) -> Dict[str, str]:
        """Get status of all external services"""
        validation = self.validate_config()
        status = {}
        
        for service, is_valid in validation.items():
            status[service] = "configured" if is_valid else "not_configured"
        
        return status


# Global configuration instance
config = ExternalServicesConfig() 