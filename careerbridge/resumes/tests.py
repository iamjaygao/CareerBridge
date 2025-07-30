from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Resume, ResumeComparison, UserDataConsent, DataRetentionPolicy
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
