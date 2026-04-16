from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from external_services.utils import get_circuit_breaker, _service_breakers, _service_metrics
from unittest.mock import patch
import requests
from django.urls import reverse
from django.utils import timezone
from rest_framework.settings import api_settings

class LegalEndpointsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_export_flow_status_none_then_accepted(self):
        status_url = reverse('resumes:data-export-status')
        r0 = self.client.get(status_url)
        self.assertEqual(r0.status_code, 200)
        self.assertIn('status', r0.data)

        export_url = reverse('resumes:data-export')
        r1 = self.client.post(export_url)
        self.assertIn(r1.status_code, (200, 202))
        self.assertIn('job_id', r1.data)

    @patch('careerbridge.external_services.utils.requests.request')
    def test_circuit_breaker_opens_on_failures(self, mock_request):
        # Force 5 consecutive failures to trip breaker
        mock_request.side_effect = requests.exceptions.RequestException('fail')
        from external_services.utils import make_api_request
        service = 'test_service'
        for _ in range(5):
            with self.assertRaises(Exception):
                make_api_request(url='http://x', service=service)
        # Next call should raise circuit open
        with self.assertRaises(Exception) as cm:
            make_api_request(url='http://x', service=service)
        self.assertIn('Circuit open', str(cm.exception))

    @patch('ats_signals.external_services.ExternalServiceManager.crawl_and_store_jobs')
    def test_external_job_crawler_502_on_error(self, mock_crawl):
        mock_crawl.side_effect = Exception('downstream')
        url = reverse('resumes:external-job-crawl')
        r = self.client.post(url, {'job_title': 'DS', 'location': 'SF'}, format='json')
        self.assertEqual(r.status_code, 502)
        self.assertTrue(r.data.get('fallback'))
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Resume, ResumeComparison, UserDataConsent, DataRetentionPolicy, LegalDisclaimer
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal

# Create your tests here.

class ResumeModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_resume_creation(self):
        # Create a mock resume file
        resume_file = SimpleUploadedFile('test_resume.pdf', b'PDF content', content_type='application/pdf')
        resume = Resume.objects.create(
            user=self.user,
            title='Test Resume',
            file=resume_file,
            file_size=resume_file.size,
            file_type='pdf',
        )
        self.assertEqual(resume.title, 'Test Resume')
        self.assertEqual(resume.user.username, 'testuser')
        self.assertEqual(resume.file_type, 'pdf')
        # Check if filename contains original filename (Django may add prefix or suffix)
        self.assertIn('test_resume', resume.file.name)
        self.assertTrue(resume.file.name.endswith('.pdf'))

class ResumeComparisonTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.resume1 = Resume.objects.create(
            user=self.user,
            title='Resume 1',
            file=SimpleUploadedFile('resume1.pdf', b'PDF content 1', content_type='application/pdf'),
            file_size=100,
            file_type='pdf',
        )
        self.resume2 = Resume.objects.create(
            user=self.user,
            title='Resume 2',
            file=SimpleUploadedFile('resume2.pdf', b'PDF content 2', content_type='application/pdf'),
            file_size=100,
            file_type='pdf',
        )

    def test_resume_comparison_creation(self):
        comparison = ResumeComparison.objects.create(
            user=self.user,
            title='Test Comparison',
            description='Comparing two resumes',
            comparison_type='version',
            overall_improvement=Decimal('15.50'),
            score_changes={'content': 10, 'format': 5},
            improvement_areas=['Better formatting', 'More keywords'],
            maintained_strengths=['Good experience section'],
            new_weaknesses=['Could add more achievements'],
        )
        
        # Add resume to comparison
        comparison.resumes.add(self.resume1, self.resume2)
        
        self.assertEqual(comparison.title, 'Test Comparison')
        self.assertEqual(comparison.comparison_type, 'version')
        self.assertEqual(comparison.overall_improvement, Decimal('15.50'))
        self.assertEqual(comparison.resumes.count(), 2)
        self.assertIn(self.resume1, comparison.resumes.all())
        self.assertIn(self.resume2, comparison.resumes.all())

class UserDataConsentTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_user_data_consent_creation(self):
        # Create multiple consent records, each corresponding to a consent type
        consent1 = UserDataConsent.objects.create(
            user=self.user,
            consent_type='data_collection',
            is_granted=True,
            consent_version='1.0',
        )
        
        consent2 = UserDataConsent.objects.create(
            user=self.user,
            consent_type='data_processing',
            is_granted=True,
            consent_version='1.0',
        )
        
        consent3 = UserDataConsent.objects.create(
            user=self.user,
            consent_type='data_sharing',
            is_granted=False,
            consent_version='1.0',
        )
        
        self.assertEqual(consent1.user, self.user)
        self.assertEqual(consent1.consent_type, 'data_collection')
        self.assertTrue(consent1.is_granted)
        
        self.assertEqual(consent2.consent_type, 'data_processing')
        self.assertTrue(consent2.is_granted)
        
        self.assertEqual(consent3.consent_type, 'data_sharing')
        self.assertFalse(consent3.is_granted)

class DataRetentionPolicyTest(TestCase):
    def test_data_retention_policy_creation(self):
        policy = DataRetentionPolicy.objects.create(
            data_type='resume_files',
            retention_period_days=365,
            auto_delete=True,
            anonymize_before_delete=True,
        )
        
        self.assertEqual(policy.data_type, 'resume_files')
        self.assertEqual(policy.retention_period_days, 365)
        self.assertTrue(policy.auto_delete)
        self.assertTrue(policy.anonymize_before_delete)


class ConsentEndpointsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='consentuser', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        resume_file = SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        self.resume = Resume.objects.create(
            user=self.user,
            title='Resume',
            file=resume_file,
            file_size=resume_file.size,
            file_type='pdf',
        )
        self.disclaimer = LegalDisclaimer.objects.create(
            disclaimer_type='resume_analysis',
            title='Resume Analysis Disclaimer',
            content='Test disclaimer',
            version='1.0',
            is_active=True,
            effective_date=timezone.now().date(),
            requires_consent=True,
        )

    def test_missing_consent_returns_403(self):
        url = reverse('resumes:resume-analyze')
        response = self.client.post(url, {'resume_id': self.resume.id}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertIn('required_disclaimers', response.data)

    def test_grant_consent_endpoint(self):
        url = reverse('resumes:data-consent')
        response = self.client.post(
            url,
            {'consent_type': 'data_processing', 'disclaimer_types': ['resume_analysis']},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        consent_types = [c['consent_type'] for c in response.data.get('data_consents', [])]
        self.assertIn('data_processing', consent_types)

    @override_settings(
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_RATES': {
                'user': '1000/day',
                'anon': '100/day',
                'burst': '20/min',
                'ai_analysis': '1/min',
            },
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.UserRateThrottle',
                'rest_framework.throttling.AnonRateThrottle',
            ],
        }
    )
    def test_ai_analysis_throttle(self):
        api_settings.reload()
        from django.core.cache import cache
        cache.clear()
        url = reverse('resumes:resume-analyze')
        first = self.client.post(
            url,
            {'resume_id': self.resume.id, 'consent': True, 'consent_version': '1.0'},
            format='json'
        )
        self.assertIn(first.status_code, (200, 400))
        second = self.client.post(
            url,
            {'resume_id': self.resume.id, 'consent': True, 'consent_version': '1.0'},
            format='json'
        )
        self.assertEqual(second.status_code, 429)
