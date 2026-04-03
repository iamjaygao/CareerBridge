#!/usr/bin/env python3
"""
Quick governance test script to verify implementation.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/kinko/WORKSPACE/projects/careerbridge/CareerBridge/gateai')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from django.contrib.auth import get_user_model
from kernel.governance.models import PlatformState, FeatureFlag, GovernanceAudit

User = get_user_model()

print("=" * 80)
print("GOVERNANCE IMPLEMENTATION TEST")
print("=" * 80)

# Test 1: Create superuser if doesn't exist
superuser = User.objects.filter(is_superuser=True).first()
if not superuser:
    superuser = User.objects.create_user(
        username='testsuper',
        email='super@test.com',
        password='testpass123',
        is_superuser=True,
        is_staff=True
    )
    print("✓ Created test superuser")
else:
    print(f"✓ Using existing superuser: {superuser.username}")

# Test 2: Create PlatformState
platform_state, created = PlatformState.objects.get_or_create(
    defaults={
        'state': 'SINGLE_WORKLOAD',
        'active_workloads': ['PEER_MOCK'],
        'frozen_modules': [
            'MENTOR', 'PAYMENT', 'AI', 'MATCHFORGE', 'MARKETPLACE',
            'APPOINTMENTS', 'CHAT', 'SEARCH', 'DASHBOARD',
            'JOB_CRAWLER', 'RESUME_MATCHER', 'ATS_SIGNALS',
            'SIGNAL_DELIVERY', 'ENGINES'
        ],
        'reason': 'Phase-A Peer Mock Only (Test)',
        'updated_by': superuser
    }
)

if created:
    print("✓ Created PlatformState")
else:
    print(f"✓ PlatformState exists (version: {platform_state.governance_version})")

# Test 3: Create Feature Flags
feature_config = {
    'USERS': ('ON', 'user'),
    'KERNEL_ADMIN': ('ON', 'internal'),
    'DECISION_SLOTS': ('ON', 'internal'),
    'HUMAN_LOOP': ('ON', 'internal'),
    'PEER_MOCK': ('ON', 'user'),
    'APPOINTMENTS': ('OFF', 'internal'),
    'PAYMENTS': ('OFF', 'internal'),
    'CHAT': ('OFF', 'internal'),
    'SEARCH': ('OFF', 'internal'),
}

flags_created = 0
for key, (state, visibility) in feature_config.items():
    flag, created = FeatureFlag.objects.get_or_create(
        key=key,
        defaults={
            'state': state,
            'visibility': visibility,
            'reason': f'Phase-A configuration - {key}',
            'updated_by': superuser,
        }
    )
    if created:
        flags_created += 1

print(f"✓ Created {flags_created} new feature flags")
print(f"✓ Total feature flags: {FeatureFlag.objects.count()}")

# Test 4: Create audit entry
GovernanceAudit.objects.create(
    action='GOVERNANCE_INIT',
    payload={
        'test': True,
        'flags_created': flags_created,
    },
    reason='Test governance initialization',
    actor=superuser
)
print("✓ Created audit entry")

# Test 5: Display governance state
print("\n" + "=" * 80)
print("GOVERNANCE STATE")
print("=" * 80)
print(f"Platform State: {platform_state.state}")
print(f"Active Workloads: {', '.join(platform_state.active_workloads)}")
print(f"Governance Version: {platform_state.governance_version}")
print(f"\nFeature Flags:")

for flag in FeatureFlag.objects.order_by('key'):
    status_icon = "🟢" if flag.state == "ON" else "🔴" if flag.state == "OFF" else "🟡"
    print(f"  {status_icon} {flag.key}: {flag.state} ({flag.visibility})")

print("\n" + "=" * 80)
print("✅ GOVERNANCE IMPLEMENTATION TEST PASSED")
print("=" * 80)
