"""
Kernel Console Smoke Tests

Quick verification that kernel console endpoints are working correctly.
Run with: python manage.py test kernel.console.test_console
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from kernel.governance.models import FeatureFlag, PlatformState
import json

User = get_user_model()


class KernelConsoleAccessTest(TestCase):
    """Test kernel console access control"""
    
    def setUp(self):
        """Create test users"""
        # Superuser (should have access)
        self.superuser = User.objects.create_user(
            username='root',
            email='root@kernel.ai',
            password='test123',
            is_superuser=True,
            is_staff=True
        )
        
        # Staff user (should NOT have access)
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='test123',
            is_staff=True,
            is_superuser=False
        )
        
        # Regular user (should NOT have access)
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='test123'
        )
        
        # Create platform state
        PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            reason='Test setup',
            updated_by=self.superuser
        )
        
        # Create test feature flag
        FeatureFlag.objects.create(
            key='TEST_FLAG',
            state='OFF',
            visibility='internal',
            reason='Test flag',
            updated_by=self.superuser
        )
        
        self.client = Client()
    
    def test_superuser_can_access_status(self):
        """Superuser should be able to access kernel console status"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['kernel_online'])
        self.assertEqual(data['world'], 'kernel')
    
    def test_superuser_can_access_flags(self):
        """Superuser should be able to view feature flags"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/console/flags/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_superuser_can_access_world_map(self):
        """Superuser should be able to view world map"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/console/world-map/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('worlds', data)
        self.assertEqual(data['current_world'], 'kernel')
    
    def test_superuser_can_access_users(self):
        """Superuser should be able to view superuser list"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/console/users/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
    
    def test_staff_user_denied_access(self):
        """Staff user (non-superuser) should be denied access"""
        self.client.force_login(self.staff_user)
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 403)
    
    def test_regular_user_denied_access(self):
        """Regular user should be denied access"""
        self.client.force_login(self.regular_user)
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 403)
    
    def test_unauthenticated_denied_access(self):
        """Unauthenticated request should be denied access"""
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 403)


class KernelConsoleOperationsTest(TestCase):
    """Test kernel console operations"""
    
    def setUp(self):
        """Create superuser and test data"""
        self.superuser = User.objects.create_user(
            username='root',
            email='root@kernel.ai',
            password='test123',
            is_superuser=True,
            is_staff=True
        )
        
        # Create platform state
        PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            reason='Test setup',
            updated_by=self.superuser
        )
        
        # Create test feature flags
        FeatureFlag.objects.create(
            key='FLAG_A',
            state='OFF',
            visibility='internal',
            reason='Test flag A',
            updated_by=self.superuser
        )
        FeatureFlag.objects.create(
            key='FLAG_B',
            state='ON',
            visibility='internal',
            reason='Test flag B',
            updated_by=self.superuser
        )
        
        self.client = Client()
        self.client.force_login(self.superuser)
    
    def test_can_update_feature_flags(self):
        """Superuser should be able to update feature flags"""
        payload = {
            'FLAG_A': 'ON',
            'FLAG_B': 'BETA'
        }
        response = self.client.post(
            '/kernel/console/flags/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify updates
        flag_a = FeatureFlag.objects.get(key='FLAG_A')
        flag_b = FeatureFlag.objects.get(key='FLAG_B')
        self.assertEqual(flag_a.state, 'ON')
        self.assertEqual(flag_b.state, 'BETA')
        self.assertEqual(flag_a.updated_by, self.superuser)
    
    def test_invalid_state_ignored(self):
        """Invalid state values should be ignored"""
        payload = {
            'FLAG_A': 'INVALID_STATE'
        }
        response = self.client.post(
            '/kernel/console/flags/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Flag should remain unchanged
        flag_a = FeatureFlag.objects.get(key='FLAG_A')
        self.assertEqual(flag_a.state, 'OFF')
    
    def test_status_returns_platform_info(self):
        """Status endpoint should return complete platform info"""
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('governance_version', data)
        self.assertIn('platform_state', data)
        self.assertIn('active_workloads', data)
        self.assertIn('frozen_modules', data)
        self.assertEqual(data['platform_state'], 'SINGLE_WORKLOAD')
        self.assertEqual(data['active_workloads'], ['PEER_MOCK'])


class KernelConsoleWorldIntegrationTest(TestCase):
    """Test kernel console integration with 4-World OS"""
    
    def setUp(self):
        """Create superuser"""
        self.superuser = User.objects.create_user(
            username='root',
            email='root@kernel.ai',
            password='test123',
            is_superuser=True,
            is_staff=True
        )
        
        self.client = Client()
        self.client.force_login(self.superuser)
    
    def test_kernel_world_detected(self):
        """Kernel console should be detected as kernel world"""
        response = self.client.get('/kernel/console/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['world'], 'kernel')
    
    def test_world_map_shows_all_worlds(self):
        """World map should show all 4 worlds"""
        response = self.client.get('/kernel/console/world-map/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        worlds = data['worlds']
        self.assertIn('public', worlds)
        self.assertIn('app', worlds)
        self.assertIn('admin', worlds)
        self.assertIn('kernel', worlds)
        
        # Verify kernel namespace includes console
        kernel_namespaces = worlds['kernel']
        self.assertIn('/kernel/console', kernel_namespaces)
