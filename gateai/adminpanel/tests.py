from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import SystemStats, AdminAction, SystemConfig, DataExport, ContentModeration
from signal_delivery.models import NotificationTemplate

User = get_user_model()

class SystemStatsTest(TestCase):
    """System statistics test"""
    
    def test_system_stats_creation(self):
        """Test system statistics creation"""
        stats = SystemStats.objects.create(
            total_users=100,
            active_users_today=50,
            new_users_today=10,
            total_mentors=20,
            active_mentors=15,
            pending_mentor_applications=5,
            total_appointments=200,
            appointments_today=25,
            completed_appointments=150,
            cancelled_appointments=25,
            total_resumes=300,
            resumes_analyzed_today=30,
            total_revenue=5000.00,
            revenue_today=500.00,
            avg_response_time=150.5,
            error_rate=0.5,
            uptime_percentage=99.9
        )
        
        self.assertEqual(stats.total_users, 100)
        self.assertEqual(stats.active_users_today, 50)
        self.assertEqual(stats.total_revenue, 5000.00)
        self.assertEqual(stats.avg_response_time, 150.5)
        self.assertEqual(stats.uptime_percentage, 99.9)

class AdminActionTest(TestCase):
    """Admin action test"""
    
    def setUp(self):
        """Setup test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_admin_action_creation(self):
        """Test admin action creation"""
        action = AdminAction.objects.create(
            admin_user=self.admin_user,
            action_type='user_management',
            action_description='Test admin action',
            target_model='User',
            target_id=1,
            action_data={'action': 'create', 'user_id': 1},
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(action.admin_user, self.admin_user)
        self.assertEqual(action.action_type, 'user_management')
        self.assertEqual(action.target_model, 'User')
        self.assertEqual(action.target_id, 1)
        self.assertEqual(action.ip_address, '127.0.0.1')

class SystemConfigTest(TestCase):
    """System configuration test"""
    
    def setUp(self):
        """Setup test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_system_config_creation(self):
        """Test system configuration creation"""
        config = SystemConfig.objects.create(
            key='test_config',
            value='test_value',
            config_type='general',
            description='Test configuration',
            is_active=True,
            is_sensitive=False,
            updated_by=self.admin_user
        )
        
        self.assertEqual(config.key, 'test_config')
        self.assertEqual(config.value, 'test_value')
        self.assertEqual(config.config_type, 'general')
        self.assertTrue(config.is_active)
        self.assertFalse(config.is_sensitive)
        self.assertEqual(config.updated_by, self.admin_user)

class DataExportTest(TestCase):
    """Data export test"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='email',
            notification_type='appointment_reminder',
            title_template='Test',
            message_template='Test'
        )
    
    def test_data_export_creation(self):
        """Test data export creation"""
        export = DataExport.objects.create(
            name='Test Export',
            export_type='users',
            format='csv',
            requested_by=self.user,
            date_from=timezone.now().date(),
            date_to=timezone.now().date(),
            filters={'status': 'active'}
        )
        
        self.assertEqual(export.name, 'Test Export')
        self.assertEqual(export.export_type, 'users')
        self.assertEqual(export.format, 'csv')
        self.assertEqual(export.requested_by, self.user)
        self.assertEqual(export.status, 'pending')
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        export = DataExport.objects.create(
            name='Test Export',
            export_type='users',
            format='csv',
            requested_by=self.user
        )
        
        # Manually set progress-related fields
        export.total_count = 100
        export.sent_count = 50
        export.failed_count = 10
        export.save()
        
        # Progress should be (50 + 10) / 100 * 100 = 60%
        self.assertEqual(export.progress_percentage, 60.0)

class ContentModerationTest(TestCase):
    """Content moderation test"""
    
    def setUp(self):
        """Setup test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
    
    def test_content_moderation_creation(self):
        """Test content moderation creation"""
        moderation = ContentModeration.objects.create(
            content_type='mentor_profile',
            content_id=1,
            content_preview='Test mentor profile content',
            status='pending',
            flagged_reason='Test flag reason',
            moderation_notes='Test moderation notes'
        )
        
        self.assertEqual(moderation.content_type, 'mentor_profile')
        self.assertEqual(moderation.content_id, 1)
        self.assertEqual(moderation.status, 'pending')
        self.assertEqual(moderation.flagged_reason, 'Test flag reason')
        self.assertEqual(moderation.moderation_notes, 'Test moderation notes')
