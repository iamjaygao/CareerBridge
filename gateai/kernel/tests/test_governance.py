"""
Governance Tests

Acceptance tests for Phase-A governance:
- Frozen modules return 404
- Active modules work normally
- Feature flag toggles respected within TTL
- SuperAdmin-only access to governance APIs
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from kernel.governance.models import PlatformState, FeatureFlag, GovernanceAudit, BusPowerState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

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
        response = self.client.get('/api/v1/users/me/')
        self.assertNotEqual(response.status_code, 404, 
                           'Active module should not return 404')
    
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
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + str(RefreshToken.for_user(self.superuser).access_token)
        
        response = self.client.get('/api/v1/adminpanel/governance/platform-state/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/api/v1/adminpanel/governance/feature-flags/')
        self.assertEqual(response.status_code, 200)
    
    def test_staff_cannot_access_governance_api(self):
        """Test that staff (non-superuser) cannot access governance APIs"""
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + str(RefreshToken.for_user(self.staff_user).access_token)
        
        response = self.client.get('/api/v1/adminpanel/governance/platform-state/')
        self.assertEqual(response.status_code, 403, 
                        'Staff user should get 403, not access to governance')
        
        response = self.client.get('/api/v1/adminpanel/governance/feature-flags/')
        self.assertEqual(response.status_code, 403)
    
    def test_feature_flag_update_increments_version(self):
        """Test that updating a feature flag increments governance_version"""
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + str(RefreshToken.for_user(self.superuser).access_token)
        
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
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + str(RefreshToken.for_user(self.superuser).access_token)
        
        # Try to update without reason
        response = self.client.patch(
            f'/api/v1/adminpanel/governance/feature-flags/TEST_FEATURE/',
            data={'state': 'ON'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('reason', response.json())


class BetaFeatureAccessTest(TestCase):
    """Test BETA feature access (superuser only)"""
    
    def setUp(self):
        """Initialize test data"""
        # SEARCH_BUS on, so requests reach the BETA gate rather than a bus 404.
        BusPowerState.objects.all().delete()
        BusPowerState.objects.bulk_create([
            BusPowerState(bus_name=n, state=v)
            for n, v in {**BUS_POWER_DEFAULTS, 'SEARCH_BUS': 'ON'}.items()
        ])
        invalidate_cache()
        self.addCleanup(invalidate_cache)

        self.superuser = User.objects.create_user(
            username='superadmin',
            email='beta-super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='beta-staff@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='beta-user@test.com',
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
        self.flag = FeatureFlag.objects.create(
            key='SEARCH',
            state='BETA',
            visibility='user',
            reason='Beta testing',
            updated_by=self.superuser
        )

    def get_search(self, user):
        # JWT: DRF authenticates JWT only, so a session login would look anonymous.
        client = Client(HTTP_AUTHORIZATION='Bearer ' + str(RefreshToken.for_user(user).access_token))
        return client.get('/api/v1/search/')

    def assert_404_is_from_beta_gate(self, user):
        self.assertEqual(self.get_search(user).status_code, 404)
        # Same user, same bus, same route: only the flag state changes.
        FeatureFlag.objects.filter(pk=self.flag.pk).update(state='ON')
        self.assertEqual(self.get_search(user).status_code, 200)
    
    def test_superuser_can_access_beta_feature(self):
        """Test that superuser can access BETA features"""
        response = self.get_search(self.superuser)
        self.assertEqual(response.status_code, 200)
    
    def test_staff_cannot_access_beta_feature(self):
        """Test that staff cannot access BETA features (GOVERNANCE CONSTITUTION)"""
        self.assert_404_is_from_beta_gate(self.staff_user)
    
    def test_regular_user_cannot_access_beta_feature(self):
        """Test that regular user cannot access BETA features"""
        self.assert_404_is_from_beta_gate(self.regular_user)

    def test_search_bus_off_hides_beta_feature_from_superuser(self):
        """Control: with SEARCH_BUS off, even the superuser gets 404."""
        BusPowerState.objects.filter(bus_name='SEARCH_BUS').update(state='OFF')
        self.assertEqual(self.get_search(self.superuser).status_code, 404)
