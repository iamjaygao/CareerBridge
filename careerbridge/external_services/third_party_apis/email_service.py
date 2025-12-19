"""
Email Service Integration

This module provides integration with various email service providers
including SendGrid, AWS SES, and SMTP for sending notifications and updates.
"""

import logging
from typing import Dict, List, Any, Optional
import requests
from django.conf import settings

from ..config import config
from ..utils import (
    retry_on_failure, 
    log_api_call, 
    ExternalServiceError, 
    make_api_request,
    create_headers
)

logger = logging.getLogger(__name__)


class EmailService:
    """Email service integration with multiple providers"""
    
    def __init__(self):
        self.provider = config.email.provider
        self.api_key = config.email.api_key
        self.from_email = config.email.from_email
        self.from_name = config.email.from_name
        self.template_id = config.email.template_id
        
        if not self.api_key:
            logger.warning("Email service API key not configured")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    @log_api_call("SendGrid", "mail/send", "POST")
    def send_email_sendgrid(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        template_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email using SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML or plain text)
            template_data: Template variables for dynamic content
        
        Returns:
            SendGrid API response
        """
        if not self.api_key:
            raise ExternalServiceError("SendGrid API key not configured", "sendgrid")
        
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = create_headers(self.api_key)
        
        # Prepare email data
        email_data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": self.from_email,
                "name": self.from_name
            },
            "content": [
                {
                    "type": "text/html",
                    "value": content
                }
            ]
        }
        
        # Add template if specified
        if self.template_id:
            email_data["template_id"] = self.template_id
            if template_data:
                email_data["personalizations"][0]["dynamic_template_data"] = template_data
        
        try:
            response = make_api_request(
                url=url,
                method="POST",
                headers=headers,
                data=email_data,
                service="SendGrid"
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return response
            
        except Exception as e:
            logger.error(f"SendGrid email sending failed: {e}")
            raise ExternalServiceError(f"Email sending failed: {e}", "sendgrid")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    @log_api_call("AWS SES", "send", "POST")
    def send_email_ses(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        template_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email using AWS SES
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content
            template_data: Template variables
        
        Returns:
            AWS SES API response
        """
        # This would require boto3 for AWS SES integration
        # For now, we'll implement a placeholder
        logger.info(f"AWS SES email to {to_email}: {subject}")
        
        return {
            "message_id": "ses-message-id",
            "status": "sent"
        }
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        template_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email using configured provider
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content
            template_data: Template variables
        
        Returns:
            Provider-specific response
        """
        if self.provider == "sendgrid":
            return self.send_email_sendgrid(to_email, subject, content, template_data)
        elif self.provider == "ses":
            return self.send_email_ses(to_email, subject, content, template_data)
        else:
            raise ExternalServiceError(f"Unsupported email provider: {self.provider}", "email")
    
    def send_notification_email(
        self, 
        to_email: str, 
        notification_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification email with predefined templates
        
        Args:
            to_email: Recipient email address
            notification_type: Type of notification
            data: Notification data
        
        Returns:
            Email sending result
        """
        templates = {
            "appointment_confirmation": {
                "subject": "Appointment Confirmed - CareerBridge",
                "template": "appointment_confirmation.html"
            },
            "resume_analysis_ready": {
                "subject": "Your Resume Analysis is Ready - CareerBridge",
                "template": "resume_analysis_ready.html"
            },
            "interview_reminder": {
                "subject": "Interview Reminder - CareerBridge",
                "template": "interview_reminder.html"
            },
            "welcome": {
                "subject": "Welcome to CareerBridge!",
                "template": "welcome.html"
            }
        }
        
        if notification_type not in templates:
            raise ExternalServiceError(f"Unknown notification type: {notification_type}", "email")
        
        template = templates[notification_type]
        subject = template["subject"]
        
        # For now, use simple HTML content
        # In production, you'd load actual HTML templates
        content = self._generate_email_content(notification_type, data)
        
        return self.send_email(to_email, subject, content, data)
    
    def _generate_email_content(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Generate email content based on notification type"""
        if notification_type == "appointment_confirmation":
            return f"""
            <html>
            <body>
                <h2>Appointment Confirmed</h2>
                <p>Hello {data.get('user_name', 'there')},</p>
                <p>Your appointment with {data.get('mentor_name', 'your mentor')} has been confirmed.</p>
                <p><strong>Date:</strong> {data.get('appointment_date', 'TBD')}</p>
                <p><strong>Time:</strong> {data.get('appointment_time', 'TBD')}</p>
                <p><strong>Type:</strong> {data.get('appointment_type', 'Session')}</p>
                <p>Please join the meeting at the scheduled time.</p>
                <p>Best regards,<br>CareerBridge Team</p>
            </body>
            </html>
            """
        
        elif notification_type == "resume_analysis_ready":
            return f"""
            <html>
            <body>
                <h2>Resume Analysis Complete</h2>
                <p>Hello {data.get('user_name', 'there')},</p>
                <p>Your resume analysis is ready! Here's a summary:</p>
                <p><strong>Overall Score:</strong> {data.get('score', 'N/A')}/100</p>
                <p><strong>Key Strengths:</strong> {', '.join(data.get('strengths', []))}</p>
                <p><strong>Areas for Improvement:</strong> {', '.join(data.get('weaknesses', []))}</p>
                <p>Log in to your account to view the full analysis and recommendations.</p>
                <p>Best regards,<br>CareerBridge Team</p>
            </body>
            </html>
            """
        
        elif notification_type == "interview_reminder":
            return f"""
            <html>
            <body>
                <h2>Interview Reminder</h2>
                <p>Hello {data.get('user_name', 'there')},</p>
                <p>This is a reminder for your upcoming interview:</p>
                <p><strong>Company:</strong> {data.get('company', 'N/A')}</p>
                <p><strong>Position:</strong> {data.get('position', 'N/A')}</p>
                <p><strong>Date:</strong> {data.get('interview_date', 'TBD')}</p>
                <p><strong>Time:</strong> {data.get('interview_time', 'TBD')}</p>
                <p>Good luck with your interview!</p>
                <p>Best regards,<br>CareerBridge Team</p>
            </body>
            </html>
            """
        
        elif notification_type == "welcome":
            return f"""
            <html>
            <body>
                <h2>Welcome to CareerBridge!</h2>
                <p>Hello {data.get('user_name', 'there')},</p>
                <p>Welcome to CareerBridge! We're excited to help you advance your career.</p>
                <p>Here's what you can do to get started:</p>
                <ul>
                    <li>Upload your resume for AI-powered analysis</li>
                    <li>Browse and book sessions with experienced mentors</li>
                    <li>Practice with mock interviews</li>
                    <li>Get personalized job recommendations</li>
                </ul>
                <p>Best regards,<br>CareerBridge Team</p>
            </body>
            </html>
            """
        
        return "<p>Email content not available.</p>"
    
    def check_health(self) -> Dict[str, Any]:
        """Check email service health"""
        try:
            if not self.api_key:
                return {
                    "status": "unhealthy",
                    "error": "API key not configured"
                }
            
            # For SendGrid, we can check the API key validity
            if self.provider == "sendgrid":
                url = "https://api.sendgrid.com/v3/user/profile"
                headers = create_headers(self.api_key)
                
                response = make_api_request(
                    url=url,
                    method="GET",
                    headers=headers,
                    service="SendGrid"
                )
                
                return {
                    "status": "healthy",
                    "provider": self.provider,
                    "account": response.get("email", "unknown")
                }
            
            return {
                "status": "healthy",
                "provider": self.provider
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance， 先不启动，等待下一步完善后再启用 
# email_service = EmailService() 