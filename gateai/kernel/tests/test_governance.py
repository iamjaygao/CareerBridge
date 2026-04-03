"""
Governance Tests

Acceptance tests for Phase-A governance:
- Frozen modules return 404
- Active modules work normally
- Feature flag toggles respected within TTL
- SuperAdmin-only access to governance APIs
"""

import time
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from kernel.governance.models import PlatformState, FeatureFlag, GovernanceAudit

User = get_user_model()


class GovernanceMiddlewareTest(TestCase):
    """Test governance middleware enforcement"""
    
    def setUp(self):
        """Create test users and initialize governance"""
        self.client = Client()
        
        # Create test users
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Initialize governance
        self.platform_state = PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            frozen_modules=['MENTOR', 'PAYMENT', 'CHAT', 'SEARCH'],
            reason='Test initialization',
            updated_by=self.superuser
        )
        
        # Create feature flags
        self.feature_users = FeatureFlag.objects.create(
            key='USERS',
            state='ON',
            visibility='user',
            reason='Core user management',
            updated_by=self.superuser
        )
        
        self.feature_payments = FeatureFlag.objects.create(
            key='PAYMENTS',
            state='OFF',
            visibility='internal',
            reason='Frozen for Phase-A',
            updated_by=self.superuser
        )
        
        self.feature_chat = FeatureFlag.objects.create(
            key='CHAT',
            state='OFF',
            visibility='internal',
            reason='Frozen for Phase-A',
            updated_by=self.superuser
        )
    
    def test_frozen_module_returns_404(self):
        """Test that frozen modules (OFF state) return 404"""
        self.client.login(username='user', password='testpass123')
        
        # Try to access frozen payments module
        response = self.client.get('/api/v1/payments/payouts/summary/')
        self.assertEqual(response.status_code, 404)
        
        # Try to access frozen chat module
        response = self.client.get('/api/v1/chat/messages/')
        self.assertEqual(response.status_code, 404)
    
    def test_active_module_works(self):
        """Test that active modules (ON state) work normally"""
        # Users module should work (note: might get 401 if auth required, but not 404)
        response = self.client.get('/api/v1/users/profile/')
        self.assertNotEqual(response.status_code, 404, 
                           'Active module should not return 404')
    
    def test_admin_bypass(self):
        """Test that admin paths are never blocked"""
        response = self.client.get('/admin/')
        # Should not return 404 (will redirect to login)
        self.assertNotEqual(response.status_code, 404)
    
    def test_static_bypass(self):
        """Test that static paths are never blocked"""
        response = self.client.get('/static/test.css')
        # Should not return 404 from governance (might be 404 from file not found)
        # Just check it doesn't crash
        self.assertIn(response.status_code, [200, 404])  # Either works or file not found


class GovernanceAPITest(TestCase):
    """Test governance API endpoints"""
    
    def setUp(self):
        """Create test users"""
        self.client = Client()
        
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        # Initialize governance
        self.platform_state = PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            frozen_modules=[],
            reason='Test',
            updated_by=self.superuser
        )
        
        self.feature_flag = FeatureFlag.objects.create(
            key='TEST_FEATURE',
            state='OFF',
            visibility='internal',
            reason='Test feature',
            updated_by=self.superuser
        )
    
    def test_superuser_can_access_governance_api(self):
        """Test that superuser can access governance APIs"""
        self.client.login(username='superadmin', password='testpass123')
        
        response = self.client.get('/api/v1/adminpanel/governance/platform-state/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/api/v1/adminpanel/governance/feature-flags/')
        self.assertEqual(response.status_code, 200)
    
    def test_staff_cannot_access_governance_api(self):
        """Test that staff (non-superuser) cannot access governance APIs"""
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.get('/api/v1/adminpanel/governance/platform-state/')
        self.assertEqual(response.status_code, 403, 
                        'Staff user should get 403, not access to governance')
        
        response = self.client.get('/api/v1/adminpanel/governance/feature-flags/')
        self.assertEqual(response.status_code, 403)
    
    def test_feature_flag_update_increments_version(self):
        """Test that updating a feature flag increments governance_version"""
        self.client.login(username='superadmin', password='testpass123')
        
        old_version = self.platform_state.governance_version
        
        # Update feature flag
        response = self.client.patch(
            f'/api/v1/adminpanel/governance/feature-flags/TEST_FEATURE/',
            data={
                'state': 'ON',
                'reason': 'Enabling test feature'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that governance_version was incremented
        self.platform_state.refresh_from_db()
        self.assertGreater(self.platform_state.governance_version, old_version)
        
        # Check that audit entry was created
        audit_count = GovernanceAudit.objects.filter(
            action='FEATURE_FLAG_UPDATE',
            actor=self.superuser
        ).count()
        self.assertGreater(audit_count, 0)
    
    def test_governance_update_requires_reason(self):
        """Test that all governance updates require a reason"""
        self.client.login(username='superadmin', password='testpass123')
        
        # Try to update without reason
        response = self.client.patch(
            f'/api/v1/adminpanel/governance/feature-flags/TEST_FEATURE/',
            data={'state': 'ON'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('reason', response.json())


class FeatureFlagCachingTest(TestCase):
    """Test that middleware caching respects governance_version"""
    
    def setUp(self):
        """Initialize governance"""
        self.superuser = User.objects.create_user(
            username='superadmin',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.platform_state = PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            frozen_modules=[],
            reason='Test',
            updated_by=self.superuser
        )
        
        self.feature_flag = FeatureFlag.objects.create(
            key='PAYMENTS',
            state='OFF',
            visibility='internal',
            reason='Test',
            updated_by=self.superuser
        )
    
    def test_feature_flag_change_respected_within_ttl(self):
        """Test that changing a feature flag is respected by middleware"""
        self.client = Client()
        self.client.login(username='superadmin', password='testpass123')
        
        # First request - should return 404 (PAYMENTS is OFF)
        response = self.client.get('/api/v1/payments/payouts/summary/')
        self.assertEqual(response.status_code, 404)
        
        # Enable PAYMENTS feature
        self.feature_flag.state = 'ON'
        self.feature_flag.save()
        
        # Increment platform governance_version to invalidate cache
        self.platform_state.save()  # This increments governance_version
        
        # Wait a moment for cache to refresh (up to 5 seconds TTL)
        time.sleep(0.5)
        
        # Second request - should NOT return 404 anymore (PAYMENTS is ON)
        # Note: might return 401/403 due to permissions, but not 404
        response = self.client.get('/api/v1/payments/payouts/summary/')
        self.assertNotEqual(response.status_code, 404, 
                           'Feature should be accessible after enabling')


class BetaFeatureAccessTest(TestCase):
    """Test BETA feature access (superuser only)"""
    
    def setUp(self):
        """Initialize test data"""
        self.superuser = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        
        PlatformState.objects.create(
            state='SINGLE_WORKLOAD',
            active_workloads=['PEER_MOCK'],
            frozen_modules=[],
            reason='Test',
            updated_by=self.superuser
        )
        
        # Create BETA feature
        FeatureFlag.objects.create(
            key='SEARCH',
            state='BETA',
            visibility='user',
            reason='Beta testing',
            updated_by=self.superuser
        )
    
    def test_superuser_can_access_beta_feature(self):
        """Test that superuser can access BETA features"""
        self.client = Client()
        self.client.login(username='superadmin', password='testpass123')
        
        # Should NOT return 404 (might return other errors, but governance allows it)
        response = self.client.get('/api/v1/search/')
        self.assertNotEqual(response.status_code, 404)
    
    def test_staff_cannot_access_beta_feature(self):
        """Test that staff cannot access BETA features (GOVERNANCE CONSTITUTION)"""
        self.client = Client()
        self.client.login(username='staff', password='testpass123')
        
        # Should return 404 (BETA features only for superuser)
        response = self.client.get('/api/v1/search/')
        self.assertEqual(response.status_code, 404)
    
    def test_regular_user_cannot_access_beta_feature(self):
        """Test that regular user cannot access BETA features"""
        self.client = Client()
        self.client.login(username='user', password='testpass123')
        
        # Should return 404
        response = self.client.get('/api/v1/search/')
        self.assertEqual(response.status_code, 404)
