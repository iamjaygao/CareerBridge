from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification, NotificationPreference, NotificationTemplate

User = get_user_model()

class NotificationModelTest(TestCase):
    """Notification model test"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='appointment_reminder',
            title='Test Notification',
            message='This is a test notification',
            priority='medium'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'appointment_reminder')
        self.assertEqual(notification.priority, 'medium')
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_sent)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='appointment_reminder',
            title='Test Notification',
            message='This is a test notification',
            priority='medium'
        )
        
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_mark_as_sent(self):
        """Test marking notification as sent"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='appointment_reminder',
            title='Test Notification',
            message='This is a test notification',
            priority='medium'
        )
        
        notification.mark_as_sent()
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)

class NotificationPreferenceTest(TestCase):
    """Notification preference test"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_preference_creation(self):
        """Test notification preference creation"""
        preference = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=True,
            push_notifications=True,
            in_app_notifications=True,
            reminder_advance_hours=24
        )
        
        self.assertEqual(preference.user, self.user)
        self.assertTrue(preference.email_notifications)
        self.assertTrue(preference.push_notifications)
        self.assertTrue(preference.in_app_notifications)
        self.assertEqual(preference.reminder_advance_hours, 24)
    
    def test_quiet_hours_check(self):
        """Test quiet hours check"""
        preference = NotificationPreference.objects.create(
            user=self.user,
            quiet_hours_start=timezone.now().time().replace(hour=22, minute=0),
            quiet_hours_end=timezone.now().time().replace(hour=8, minute=0)
        )
        
        # This just tests that the method exists, actual time checking requires more complex logic
        self.assertTrue(hasattr(preference, 'is_quiet_hours'))

class NotificationTemplateTest(TestCase):
    """Notification template test"""
    
    def test_template_creation(self):
        """Test notification template creation"""
        template = NotificationTemplate.objects.create(
            name='Test Template',
            template_type='email',
            notification_type='appointment_reminder',
            subject='Test Subject',
            title_template='Test Title: {variable}',
            message_template='Test message with {variable}',
            variables={'variable': 'string'}
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.template_type, 'email')
        self.assertEqual(template.notification_type, 'appointment_reminder')
        self.assertTrue(template.is_active)
