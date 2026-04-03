"""
Kernel Pulse Tests - Phase-A.1

Minimum test coverage for Pulse ABI v0.1
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from kernel.models import KernelAuditLog
from decision_slots.models import ResourceLock

User = get_user_model()


class KernelPulseAccessTest(TestCase):
    """Test kernel pulse access control"""
    
    def setUp(self):
        # Superuser (should have access)
        self.superuser = User.objects.create_user(
            username='kernel_root',
            email='root@kernel.ai',
            password='test123',
            is_superuser=True,
            is_staff=True
        )
        
        # Regular user (should NOT have access)
        self.regular_user = User.objects.create_user(
            username='regular',
            email='user@test.com',
            password='test123'
        )
        
        self.client = Client()
    
    def test_unauthenticated_returns_403(self):
        """Unauthenticated request should return 403"""
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 403)
    
    def test_regular_user_returns_403(self):
        """Regular user should be denied access"""
        self.client.force_login(self.regular_user)
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 403)
    
    def test_superuser_returns_200(self):
        """Superuser should get 200 OK"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 200)
    
    def test_response_contains_pulse_abi_keys(self):
        """Response should contain all Pulse ABI v0.1 keys"""
        self.client.force_login(self.superuser)
        response = self.client.get('/kernel/pulse/summary/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check Pulse ABI v0.1 keys
        self.assertIn('pulse_version', data)
        self.assertEqual(data['pulse_version'], '0.1')
        
        self.assertIn('now', data)
        self.assertIn('kernel_state', data)
        self.assertIn('recent_syscalls', data)
        self.assertIn('counts', data)
        self.assertIn('active_locks', data)
        self.assertIn('top_errors_24h', data)
        
        # Check kernel_state structure
        kernel_state = data['kernel_state']
        self.assertIn('mode', kernel_state)
        self.assertIn('active_lock_pressure', kernel_state)
        self.assertIn('error_rate_1h', kernel_state)
        self.assertIn('chaos_safe', kernel_state)
        
        # Check counts structure
        counts = data['counts']
        self.assertIn('last_1h', counts)
        self.assertIn('last_24h', counts)


class KernelPulseDataTest(TestCase):
    """Test kernel pulse data computation"""
    
    def setUp(self):
        self.superuser = User.objects.create_user(
            username='kernel_root',
            email='root@kernel.ai',
            password='test123',
            is_superuser=True,
            is_staff=True
        )
        
        self.client = Client()
        self.client.force_login(self.superuser)
        
        # Create test data
        now = timezone.now()
        
        # Create successful syscalls
        for i in range(5):
            KernelAuditLog.objects.create(
                event_type='SYS_CLAIM',
                decision_id=f'test_decision_{i}',
                idempotency_key=f'test_idem_{i}_success',
                context_hash=f'test_hash_{i}',
                status='HANDLED',
                created_at=now - timedelta(minutes=10)
            )
        
        # Create failed syscalls
        for i in range(2):
            KernelAuditLog.objects.create(
                event_type='SYS_CLAIM',
                decision_id=f'test_decision_fail_{i}',
                idempotency_key=f'test_idem_{i}_fail',
                context_hash=f'test_hash_fail_{i}',
                status='FAILED',
                failure_reason='LOCK_CONFLICT',
                created_at=now - timedelta(minutes=5)
            )
    
    def test_recent_syscalls_returned(self):
        """Recent syscalls should be returned"""
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        recent_syscalls = data['recent_syscalls']
        
        self.assertIsInstance(recent_syscalls, list)
        self.assertGreaterEqual(len(recent_syscalls), 7)  # We created 7 logs
        
        # Check syscall structure
        if len(recent_syscalls) > 0:
            syscall = recent_syscalls[0]
            self.assertIn('at', syscall)
            self.assertIn('syscall', syscall)
            self.assertIn('outcome', syscall)
            # Verify it has one of the valid statuses
            self.assertIn(syscall['outcome'], ['EMITTED', 'HANDLED', 'FAILED', 'REJECTED'])
    
    def test_counts_computed_correctly(self):
        """Counts should be computed correctly"""
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        counts_1h = data['counts']['last_1h']
        
        # We created 7 logs in the last hour (5 HANDLED + 2 FAILED)
        self.assertGreaterEqual(counts_1h['total'], 7)
        self.assertGreaterEqual(counts_1h['success'], 5)  # HANDLED
        self.assertGreaterEqual(counts_1h['terminal'], 2)  # FAILED
    
    def test_kernel_state_mode_derivation(self):
        """Kernel state mode should be derived from error rate"""
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        kernel_state = data['kernel_state']
        
        # Check mode is one of the valid values
        self.assertIn(kernel_state['mode'], ['NORMAL', 'DEGRADED', 'LOCKED'])
        
        # Check chaos_safe aligns with mode
        if kernel_state['mode'] == 'LOCKED':
            self.assertFalse(kernel_state['chaos_safe'])
        else:
            self.assertTrue(kernel_state['chaos_safe'])
    
    def test_active_locks_structure(self):
        """Active locks should have correct structure"""
        response = self.client.get('/kernel/pulse/summary/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        active_locks = data['active_locks']
        
        self.assertIn('count', active_locks)
        self.assertIn('samples', active_locks)
        self.assertIsInstance(active_locks['samples'], list)
