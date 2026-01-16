"""
Tests for 4-World OS Architecture

Verifies world resolution logic and middleware behavior.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from kernel.worlds import (
    resolve_world,
    is_kernel_world,
    is_userland_world,
    get_world_description,
)
from kernel.governance.middleware import GovernanceMiddleware


User = get_user_model()


class WorldResolutionTest(TestCase):
    """Test world resolution logic"""
    
    def test_kernel_world_paths(self):
        """Kernel world should match superadmin and governance paths"""
        self.assertEqual(resolve_world('/superadmin'), 'kernel')
        self.assertEqual(resolve_world('/superadmin/governance'), 'kernel')
        self.assertEqual(resolve_world('/kernel'), 'kernel')
        self.assertEqual(resolve_world('/kernel/pulse'), 'kernel')
        self.assertEqual(resolve_world('/api/engines'), 'kernel')
        self.assertEqual(resolve_world('/api/v1/adminpanel/governance'), 'kernel')
    
    def test_admin_world_paths(self):
        """Admin world should match staff/admin paths"""
        self.assertEqual(resolve_world('/admin'), 'admin')
        self.assertEqual(resolve_world('/admin/users'), 'admin')
        self.assertEqual(resolve_world('/staff'), 'admin')
        self.assertEqual(resolve_world('/api/admin'), 'admin')
        self.assertEqual(resolve_world('/api/v1/adminpanel/users'), 'admin')
        self.assertEqual(resolve_world('/analytics'), 'admin')
    
    def test_app_world_paths(self):
        """App world should match user workload paths"""
        self.assertEqual(resolve_world('/app'), 'app')
        self.assertEqual(resolve_world('/student'), 'app')
        self.assertEqual(resolve_world('/student/dashboard'), 'app')
        self.assertEqual(resolve_world('/mentor'), 'app')
        self.assertEqual(resolve_world('/dashboard'), 'app')
        self.assertEqual(resolve_world('/profile'), 'app')
        self.assertEqual(resolve_world('/appointments'), 'app')
        self.assertEqual(resolve_world('/api/v1/users/'), 'app')
        self.assertEqual(resolve_world('/api/v1/appointments/'), 'app')
        self.assertEqual(resolve_world('/api/v1/chat/'), 'app')
    
    def test_public_world_paths(self):
        """Public world should match unauthenticated paths"""
        self.assertEqual(resolve_world('/'), 'public')
        self.assertEqual(resolve_world('/login'), 'public')
        self.assertEqual(resolve_world('/register'), 'public')
        self.assertEqual(resolve_world('/about'), 'public')
        self.assertEqual(resolve_world('/pricing'), 'public')
        self.assertEqual(resolve_world('/api/public'), 'public')
    
    def test_unknown_path_defaults_to_public(self):
        """Unknown paths should default to public world"""
        self.assertEqual(resolve_world('/unknown'), 'public')
        self.assertEqual(resolve_world('/random/path'), 'public')
    
    def test_world_helper_functions(self):
        """Test helper functions for world checks"""
        self.assertTrue(is_kernel_world('kernel'))
        self.assertFalse(is_kernel_world('admin'))
        
        self.assertTrue(is_userland_world('public'))
        self.assertTrue(is_userland_world('app'))
        self.assertTrue(is_userland_world('admin'))
        self.assertFalse(is_userland_world('kernel'))
        
        self.assertIn('control plane', get_world_description('kernel').lower())


class MiddlewareWorldIntegrationTest(TestCase):
    """Test middleware integration with world resolution"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = GovernanceMiddleware(get_response=lambda req: JsonResponse({'ok': True}))
        
        # Create test users
        self.superuser = User.objects.create_user(
            username='root',
            email='root@example.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )
    
    def test_kernel_access_granted_for_superuser(self):
        """Superuser should access kernel paths"""
        request = self.factory.get('/superadmin')
        request.user = self.superuser
        
        response = self.middleware(request)
        
        # Should pass through successfully
        self.assertEqual(request.world, 'kernel')
        self.assertEqual(response.status_code, 200)
    
    def test_kernel_access_denied_for_staff(self):
        """Staff admin (non-superuser) should be blocked from kernel"""
        request = self.factory.get('/superadmin')
        request.user = self.staff_admin
        
        response = self.middleware(request)
        
        # Should return 403
        self.assertEqual(request.world, 'kernel')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Kernel access denied', str(response.content))
    
    def test_kernel_access_denied_for_regular_user(self):
        """Regular user should be blocked from kernel"""
        request = self.factory.get('/kernel/pulse')
        request.user = self.regular_user
        
        response = self.middleware(request)
        
        # Should return 403
        self.assertEqual(request.world, 'kernel')
        self.assertEqual(response.status_code, 403)
    
    def test_admin_path_allowed_for_staff(self):
        """Staff admin should access admin world paths"""
        request = self.factory.get('/admin')
        request.user = self.staff_admin
        
        response = self.middleware(request)
        
        # Should pass through (actual auth is handled by Django's admin middleware)
        self.assertEqual(request.world, 'admin')
        # Admin path is in BYPASS_PATHS, so it passes through
        self.assertEqual(response.status_code, 200)
    
    def test_world_attached_to_request(self):
        """Middleware should attach world to request"""
        # Test each world
        test_cases = [
            ('/superadmin', 'kernel'),
            ('/admin', 'admin'),
            ('/student/dashboard', 'app'),
            ('/login', 'public'),
        ]
        
        for path, expected_world in test_cases:
            request = self.factory.get(path)
            request.user = self.superuser  # Use superuser to avoid 403
            
            self.middleware(request)
            
            self.assertEqual(
                request.world,
                expected_world,
                f"Path {path} should resolve to {expected_world}"
            )


class WorldPriorityTest(TestCase):
    """Test world resolution priority order"""
    
    def test_priority_order(self):
        """Kernel > Admin > App > Public priority order"""
        # If a path could match multiple worlds, most specific wins
        
        # /api/v1/adminpanel/governance should be kernel (not admin)
        self.assertEqual(resolve_world('/api/v1/adminpanel/governance'), 'kernel')
        self.assertEqual(resolve_world('/api/v1/adminpanel/governance/feature-flags'), 'kernel')
        
        # /api/v1/adminpanel/* (non-governance) should be admin
        self.assertEqual(resolve_world('/api/v1/adminpanel/users'), 'admin')
        self.assertEqual(resolve_world('/api/v1/adminpanel/tickets'), 'admin')
