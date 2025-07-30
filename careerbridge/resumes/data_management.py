import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from .models import (
    UserDataConsent, DataRetentionPolicy, UserDataDeletionRequest,
    LegalDisclaimer, UserDisclaimerConsent, Resume, ResumeAnalysis,
    ResumeFeedback, ResumeJobMatch, JobDescription, KeywordMatch,
    ResumeComparison, ResumeComparisonItem, ResumeExport,
    ServiceUsageLog
)

class DataConsentManager:
    """Manager for user data consent operations"""
    
    @staticmethod
    def grant_consent(user, consent_type: str, ip_address: str = None, user_agent: str = None):
        """Grant consent for data processing"""
        consent, created = UserDataConsent.objects.get_or_create(
            user=user,
            consent_type=consent_type,
            defaults={
                'is_granted': True,
                'granted_at': timezone.now(),
                'consent_version': '1.0',
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
        
        if not created and not consent.is_granted:
            consent.is_granted = True
            consent.granted_at = timezone.now()
            consent.revoked_at = None
            consent.ip_address = ip_address
            consent.user_agent = user_agent
            consent.save()
        
        return consent
    
    @staticmethod
    def revoke_consent(user, consent_type: str):
        """Revoke consent for data processing"""
        try:
            consent = UserDataConsent.objects.get(user=user, consent_type=consent_type)
            consent.is_granted = False
            consent.revoked_at = timezone.now()
            consent.save()
            return consent
        except UserDataConsent.DoesNotExist:
            return None
    
    @staticmethod
    def has_consent(user, consent_type: str) -> bool:
        """Check if user has granted consent"""
        try:
            consent = UserDataConsent.objects.get(user=user, consent_type=consent_type)
            return consent.is_granted and consent.revoked_at is None
        except UserDataConsent.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_consents(user) -> List[UserDataConsent]:
        """Get all consents for a user"""
        return UserDataConsent.objects.filter(user=user).order_by('-granted_at')

class DataRetentionManager:
    """Manager for data retention operations"""
    
    @staticmethod
    def get_retention_policy(data_type: str) -> Optional[DataRetentionPolicy]:
        """Get retention policy for data type"""
        try:
            return DataRetentionPolicy.objects.get(data_type=data_type)
        except DataRetentionPolicy.DoesNotExist:
            return None
    
    @staticmethod
    def get_expired_data(data_type: str) -> List:
        """Get data that has exceeded retention period"""
        policy = DataRetentionManager.get_retention_policy(data_type)
        if not policy or policy.legal_hold:
            return []
        
        cutoff_date = timezone.now() - timedelta(days=policy.retention_period_days)
        
        if data_type == 'resume_files':
            return Resume.objects.filter(created_at__lt=cutoff_date)
        elif data_type == 'analysis_results':
            return ResumeAnalysis.objects.filter(created_at__lt=cutoff_date)
        elif data_type == 'match_results':
            return ResumeJobMatch.objects.filter(created_at__lt=cutoff_date)
        elif data_type == 'user_activity':
            return ServiceUsageLog.objects.filter(timestamp__lt=cutoff_date)
        
        return []
    
    @staticmethod
    def anonymize_data(data_object, data_type: str):
        """Anonymize data before deletion"""
        if data_type == 'resume_files':
            data_object.title = f"Anonymized_Resume_{hashlib.md5(str(data_object.id).encode()).hexdigest()[:8]}"
            data_object.file.delete(save=False)
        elif data_type == 'analysis_results':
            data_object.extracted_text = "Anonymized content"
            data_object.detected_keywords = []
            data_object.missing_keywords = []
            data_object.technical_skills = []
            data_object.soft_skills = []
            data_object.job_titles = []
            data_object.companies = []
            data_object.institutions = []
        elif data_type == 'match_results':
            data_object.matched_skills = []
            data_object.missing_skills = []
            data_object.skill_gaps = []
            data_object.match_recommendations = []
            data_object.user_feedback = ""
        
        data_object.save()
    
    @staticmethod
    def cleanup_expired_data():
        """Clean up expired data based on retention policies"""
        data_types = ['resume_files', 'analysis_results', 'match_results', 'user_activity']
        
        for data_type in data_types:
            policy = DataRetentionManager.get_retention_policy(data_type)
            if not policy or not policy.auto_delete:
                continue
            
            expired_data = DataRetentionManager.get_expired_data(data_type)
            
            for data_object in expired_data:
                if policy.anonymize_before_delete:
                    DataRetentionManager.anonymize_data(data_object, data_type)
                else:
                    data_object.delete()

class DataDeletionManager:
    """Manager for user data deletion operations"""
    
    @staticmethod
    def create_deletion_request(user, request_type: str) -> UserDataDeletionRequest:
        """Create a data deletion request"""
        request = UserDataDeletionRequest.objects.create(
            user=user,
            request_type=request_type,
            status='pending'
        )
        
        # Send verification email
        DataDeletionManager._send_verification_email(request)
        
        return request
    
    @staticmethod
    def _send_verification_email(request: UserDataDeletionRequest):
        """Send verification email for deletion request"""
        try:
            subject = "Confirm Your Data Deletion Request"
            context = {
                'user': request.user,
                'request': request,
                'verification_url': f"{settings.SITE_URL}/resumes/data-deletion/verify/{request.id}/"
            }
            
            html_message = render_to_string('resumes/emails/data_deletion_verification.html', context)
            text_message = render_to_string('resumes/emails/data_deletion_verification.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False
            )
            
            request.verification_email_sent = True
            request.verification_email_sent_at = timezone.now()
            request.save()
            
        except Exception as e:
            print(f"Error sending verification email: {e}")
    
    @staticmethod
    def verify_deletion_request(request_id: int, verification_token: str) -> bool:
        """Verify deletion request"""
        try:
            request = UserDataDeletionRequest.objects.get(id=request_id)
            
            # Simple token verification (in production, use proper tokens)
            expected_token = hashlib.md5(f"{request.id}{request.user.id}".encode()).hexdigest()[:8]
            
            if verification_token == expected_token:
                request.verification_completed = True
                request.verification_completed_at = timezone.now()
                request.status = 'processing'
                request.save()
                
                # Process deletion
                DataDeletionManager._process_deletion(request)
                return True
            
            return False
            
        except UserDataDeletionRequest.DoesNotExist:
            return False
    
    @staticmethod
    def _process_deletion(request: UserDataDeletionRequest):
        """Process the actual data deletion"""
        try:
            with transaction.atomic():
                if request.request_type == 'resume_files':
                    DataDeletionManager._delete_resume_files(request.user)
                elif request.request_type == 'analysis_results':
                    DataDeletionManager._delete_analysis_results(request.user)
                elif request.request_type == 'match_results':
                    DataDeletionManager._delete_match_results(request.user)
                elif request.request_type == 'user_activity':
                    DataDeletionManager._delete_user_activity(request.user)
                elif request.request_type == 'personal_info':
                    DataDeletionManager._delete_personal_info(request.user)
                
                request.status = 'completed'
                request.processed_at = timezone.now()
                request.completion_notes = "Data deletion completed successfully"
                request.save()
                
        except Exception as e:
            request.status = 'failed'
            request.processed_at = timezone.now()
            request.completion_notes = f"Deletion failed: {str(e)}"
            request.save()
    
    @staticmethod
    def _delete_resume_files(user):
        """Delete user's resume files"""
        resumes = Resume.objects.filter(user=user)
        for resume in resumes:
            resume.file.delete(save=False)
            resume.delete()
    
    @staticmethod
    def _delete_analysis_results(user):
        """Delete user's analysis results"""
        ResumeAnalysis.objects.filter(resume__user=user).delete()
        ResumeFeedback.objects.filter(analysis__resume__user=user).delete()
    
    @staticmethod
    def _delete_match_results(user):
        """Delete user's match results"""
        ResumeJobMatch.objects.filter(resume__user=user).delete()
        KeywordMatch.objects.filter(user=user).delete()
    
    @staticmethod
    def _delete_user_activity(user):
        """Delete user's activity logs"""
        ServiceUsageLog.objects.filter(user=user).delete()
    
    @staticmethod
    def _delete_personal_info(user):
        """Delete user's personal information"""
        # This would typically involve anonymizing user profile data
        # For now, we'll just delete related data
        DataDeletionManager._delete_resume_files(user)
        DataDeletionManager._delete_analysis_results(user)
        DataDeletionManager._delete_match_results(user)
        DataDeletionManager._delete_user_activity(user)

class LegalComplianceManager:
    """Manager for legal compliance operations"""
    
    @staticmethod
    def get_active_disclaimer(disclaimer_type: str) -> Optional[LegalDisclaimer]:
        """Get active disclaimer by type"""
        try:
            return LegalDisclaimer.objects.get(
                disclaimer_type=disclaimer_type,
                is_active=True
            )
        except LegalDisclaimer.DoesNotExist:
            return None
    
    @staticmethod
    def record_disclaimer_consent(user, disclaimer: LegalDisclaimer, ip_address: str = None, user_agent: str = None):
        """Record user consent to disclaimer"""
        consent, created = UserDisclaimerConsent.objects.get_or_create(
            user=user,
            disclaimer=disclaimer,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
        return consent
    
    @staticmethod
    def has_disclaimer_consent(user, disclaimer_type: str) -> bool:
        """Check if user has consented to disclaimer"""
        try:
            disclaimer = LegalComplianceManager.get_active_disclaimer(disclaimer_type)
            if not disclaimer:
                return True  # No active disclaimer means no consent needed
            
            return UserDisclaimerConsent.objects.filter(
                user=user,
                disclaimer=disclaimer
            ).exists()
        except Exception:
            return False
    
    @staticmethod
    def get_required_disclaimers(user) -> List[LegalDisclaimer]:
        """Get disclaimers that require user consent"""
        active_disclaimers = LegalDisclaimer.objects.filter(
            is_active=True,
            requires_consent=True
        )
        
        required_disclaimers = []
        for disclaimer in active_disclaimers:
            if not LegalComplianceManager.has_disclaimer_consent(user, disclaimer.disclaimer_type):
                required_disclaimers.append(disclaimer)
        
        return required_disclaimers

class ResumeComparisonManager:
    """Manager for resume comparison operations"""
    
    @staticmethod
    def create_comparison(
        user, 
        title: str, 
        resumes: List[Resume], 
        comparison_type: str = 'version',
        description: str = ""
    ) -> ResumeComparison:
        """Create a new resume comparison"""
        comparison = ResumeComparison.objects.create(
            user=user,
            title=title,
            description=description,
            comparison_type=comparison_type
        )
        
        # Add resumes to comparison
        for i, resume in enumerate(resumes):
            ResumeComparisonItem.objects.create(
                comparison=comparison,
                resume=resume,
                order=i,
                label=f"Resume {i+1}"
            )
        
        # Perform comparison analysis
        ResumeComparisonManager._analyze_comparison(comparison)
        
        return comparison
    
    @staticmethod
    def _analyze_comparison(comparison: ResumeComparison):
        """Analyze the comparison and calculate metrics"""
        items = comparison.resumecomparisonitem_set.all().order_by('order')
        
        if len(items) < 2:
            return
        
        # Calculate scores for each resume
        scores = []
        for item in items:
            if item.resume.has_analysis:
                analysis = item.resume.analysis
                item.overall_score = analysis.overall_score
                item.structure_score = analysis.structure_score
                item.content_score = analysis.content_score
                item.keyword_score = analysis.keyword_score
                item.ats_score = analysis.ats_score
                item.save()
                
                scores.append({
                    'overall': float(analysis.overall_score),
                    'structure': float(analysis.structure_score),
                    'content': float(analysis.content_score),
                    'keyword': float(analysis.keyword_score),
                    'ats': float(analysis.ats_score)
                })
        
        if len(scores) >= 2:
            # Calculate improvements
            first_scores = scores[0]
            last_scores = scores[-1]
            
            overall_improvement = ((last_scores['overall'] - first_scores['overall']) / first_scores['overall']) * 100
            
            score_changes = {
                'overall': last_scores['overall'] - first_scores['overall'],
                'structure': last_scores['structure'] - first_scores['structure'],
                'content': last_scores['content'] - first_scores['content'],
                'keyword': last_scores['keyword'] - first_scores['keyword'],
                'ats': last_scores['ats'] - first_scores['ats']
            }
            
            # Generate improvement areas
            improvement_areas = []
            for category, change in score_changes.items():
                if change > 0:
                    improvement_areas.append(f"{category.title()} improved by {change:.1f} points")
                elif change < 0:
                    improvement_areas.append(f"{category.title()} decreased by {abs(change):.1f} points")
            
            # Update comparison
            comparison.overall_improvement = overall_improvement
            comparison.score_changes = score_changes
            comparison.improvement_areas = improvement_areas
            comparison.save()
    
    @staticmethod
    def get_user_comparisons(user) -> List[ResumeComparison]:
        """Get all comparisons for a user"""
        return ResumeComparison.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_comparison_details(comparison_id: int, user) -> Optional[ResumeComparison]:
        """Get detailed comparison information"""
        try:
            return ResumeComparison.objects.get(id=comparison_id, user=user)
        except ResumeComparison.DoesNotExist:
            return None 