"""
Management command to initialize Kernel Governance.

This command creates the initial PlatformState and FeatureFlags for Phase-A:
- Single workload mode (PEER_MOCK only)
- All commercial modules frozen
- Audit trail of initialization

Run this command after migrations:
    python manage.py kernel_init_governance

Safe to run multiple times (idempotent).
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kernel.governance.models import PlatformState, FeatureFlag, GovernanceAudit

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize Kernel Governance for Phase-A (Peer Mock Only)'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Initializing Kernel Governance...'))
        
        # Get or create system user for initialization
        system_user = self._get_system_user()
        
        # Initialize PlatformState
        platform_state = self._initialize_platform_state(system_user)
        
        # Initialize FeatureFlags
        feature_flags_created = self._initialize_feature_flags(system_user)
        
        # Create audit entry
        self._create_audit_entry(system_user, feature_flags_created)
        
        self.stdout.write(self.style.SUCCESS('✓ Governance initialization complete'))
        self.stdout.write(self.style.SUCCESS(f'  Platform State: {platform_state.state}'))
        self.stdout.write(self.style.SUCCESS(f'  Active Workloads: {platform_state.active_workloads}'))
        self.stdout.write(self.style.SUCCESS(f'  Feature Flags Created: {feature_flags_created}'))
        self.stdout.write(self.style.WARNING('  ⚠ Only PEER_MOCK workload is active'))
        self.stdout.write(self.style.WARNING('  ⚠ All commercial modules are FROZEN'))
    
    def _get_system_user(self):
        """Get or create system/superadmin user for governance initialization"""
        # Try to get first superuser
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            return superuser
        
        # If no superuser exists, create a system user
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@careerbridge.internal',
                'is_staff': True,
                'is_superuser': True,
                'is_active': False,  # Not for login
            }
        )
        if created:
            self.stdout.write(self.style.WARNING('  Created system user for governance'))
        return system_user
    
    def _initialize_platform_state(self, user):
        """Initialize or update PlatformState"""
        # Check if PlatformState already exists
        platform_state = PlatformState.objects.first()
        
        if platform_state:
            self.stdout.write(self.style.WARNING('  Platform State already exists - updating'))
            platform_state.state = 'SINGLE_WORKLOAD'
            platform_state.active_workloads = ['PEER_MOCK']
            platform_state.frozen_modules = [
                'MENTOR', 'PAYMENT', 'AI', 'MATCHFORGE', 'MARKETPLACE',
                'APPOINTMENTS', 'CHAT', 'SEARCH', 'DASHBOARD',
                'JOB_CRAWLER', 'RESUME_MATCHER', 'ATS_SIGNALS',
                'SIGNAL_DELIVERY', 'ENGINES'
            ]
            platform_state.reason = 'Phase-A Peer Mock Only (Re-initialized)'
            platform_state.updated_by = user
            platform_state.save()
        else:
            self.stdout.write(self.style.SUCCESS('  Creating Platform State'))
            platform_state = PlatformState.objects.create(
                state='SINGLE_WORKLOAD',
                active_workloads=['PEER_MOCK'],
                frozen_modules=[
                    'MENTOR', 'PAYMENT', 'AI', 'MATCHFORGE', 'MARKETPLACE',
                    'APPOINTMENTS', 'CHAT', 'SEARCH', 'DASHBOARD',
                    'JOB_CRAWLER', 'RESUME_MATCHER', 'ATS_SIGNALS',
                    'SIGNAL_DELIVERY', 'ENGINES'
                ],
                reason='Phase-A Peer Mock Only',
                updated_by=user
            )
        
        return platform_state
    
    def _initialize_feature_flags(self, user):
        """Initialize all feature flags with Phase-A configuration"""
        
        # Feature flag configuration: key -> (state, visibility, reason)
        feature_config = {
            # ACTIVE MODULES (ON)
            'USERS': ('ON', 'user', 'Core user management - always active'),
            'KERNEL_ADMIN': ('ON', 'internal', 'Superadmin control plane - always active'),
            'DECISION_SLOTS': ('ON', 'internal', 'Time locking for future use'),
            'HUMAN_LOOP': ('ON', 'internal', 'Feedback closure for future use'),
            'PEER_MOCK': ('ON', 'user', 'Phase-A primary workload'),
            
            # FROZEN MODULES (OFF)
            'APPOINTMENTS': ('OFF', 'internal', 'Frozen - Phase-A'),
            'MENTORS': ('OFF', 'internal', 'Frozen - Phase-A'),
            'PAYMENTS': ('OFF', 'internal', 'Frozen - Phase-A'),
            'CHAT': ('OFF', 'internal', 'Frozen - Phase-A'),
            'SEARCH': ('OFF', 'internal', 'Frozen - Phase-A'),
            'DASHBOARD': ('OFF', 'internal', 'Frozen - Phase-A'),
            'JOB_CRAWLER': ('OFF', 'internal', 'Frozen - Phase-A'),
            'RESUME_MATCHER': ('OFF', 'internal', 'Frozen - Phase-A'),
            'ATS_SIGNALS': ('OFF', 'internal', 'Frozen - Phase-A'),
            'SIGNAL_DELIVERY': ('OFF', 'internal', 'Frozen - Phase-A'),
            'ENGINES_SIGNAL_CORE': ('OFF', 'internal', 'Frozen - Phase-A'),
            'ENGINES_JOB_INGESTION': ('OFF', 'internal', 'Frozen - Phase-A'),
        }
        
        created_count = 0
        updated_count = 0
        
        for key, (state, visibility, reason) in feature_config.items():
            flag, created = FeatureFlag.objects.get_or_create(
                key=key,
                defaults={
                    'state': state,
                    'visibility': visibility,
                    'reason': reason,
                    'updated_by': user,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'    Created: {key} -> {state}'))
            else:
                # Update existing flag
                flag.state = state
                flag.visibility = visibility
                flag.reason = reason
                flag.updated_by = user
                flag.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'    Updated: {key} -> {state}'))
        
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}, Updated: {updated_count}'))
        return created_count
    
    def _create_audit_entry(self, user, flags_created):
        """Create governance audit entry"""
        GovernanceAudit.objects.create(
            action='GOVERNANCE_INIT',
            payload={
                'flags_created': flags_created,
                'platform_state': 'SINGLE_WORKLOAD',
                'active_workloads': ['PEER_MOCK'],
            },
            reason='Phase-A governance initialization - Peer Mock workload only',
            actor=user
        )
        self.stdout.write(self.style.SUCCESS('  Audit entry created'))
