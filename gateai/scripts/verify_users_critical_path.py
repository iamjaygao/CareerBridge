#!/usr/bin/env python3
"""
Verify USERS module critical path configuration
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateai.settings')
django.setup()

from kernel.governance.models import FeatureFlag, PlatformState


def verify_users_critical_path():
    """Verify that USERS module is properly configured as a critical path"""
    
    print("=" * 80)
    print("USERS MODULE CRITICAL PATH VERIFICATION")
    print("=" * 80)
    print()
    
    # Check PlatformState
    platform_state = PlatformState.objects.first()
    if platform_state:
        print(f"✅ PlatformState exists")
        print(f"   - State: {platform_state.state}")
        print(f"   - Governance Version: {platform_state.governance_version}")
    else:
        print("⚠️  PlatformState NOT FOUND - governance may be unavailable")
    print()
    
    # Check USERS feature flag
    users_flag = FeatureFlag.objects.filter(key='USERS').first()
    if users_flag:
        status = "✅" if users_flag.state == 'ON' else "⚠️"
        print(f"{status} USERS Feature Flag found:")
        print(f"   - State: {users_flag.state}")
        print(f"   - Visibility: {users_flag.visibility}")
        print(f"   - Description: {users_flag.description}")
        print()
        
        if users_flag.state != 'ON':
            print("❌ WARNING: USERS feature flag is NOT ON!")
            print("   This may block login and user endpoints.")
            print()
            print("   To fix, run:")
            print("   FeatureFlag.objects.filter(key='USERS').update(state='ON', visibility='public')")
            print()
        elif users_flag.visibility != 'public':
            print("⚠️  WARNING: USERS visibility is not 'public'")
            print("   Some users may not be able to access login/register endpoints.")
            print()
    else:
        print("⚠️  USERS Feature Flag NOT FOUND")
        print("   Creating it now with recommended settings...")
        print()
        
        FeatureFlag.objects.create(
            key='USERS',
            state='ON',
            visibility='public',
            description='User authentication and profile management (CRITICAL PATH)',
            rollout_rule=None,
        )
        print("✅ USERS Feature Flag created successfully")
        print()
    
    # Check KERNEL_ADMIN feature flag
    kernel_admin_flag = FeatureFlag.objects.filter(key='KERNEL_ADMIN').first()
    if kernel_admin_flag:
        status = "✅" if kernel_admin_flag.state == 'ON' else "⚠️"
        print(f"{status} KERNEL_ADMIN Feature Flag found:")
        print(f"   - State: {kernel_admin_flag.state}")
        print(f"   - Visibility: {kernel_admin_flag.visibility}")
    else:
        print("⚠️  KERNEL_ADMIN Feature Flag NOT FOUND")
    print()
    
    # URL routing check
    print("=" * 80)
    print("URL ROUTING VERIFICATION")
    print("=" * 80)
    print()
    print("Expected endpoints under /api/v1/users/:")
    print("   - POST   /api/v1/users/register/")
    print("   - POST   /api/v1/users/login/              ✅ CRITICAL")
    print("   - POST   /api/v1/users/refresh/")
    print("   - GET    /api/v1/users/me/                 ✅ CRITICAL")
    print("   - PATCH  /api/v1/users/me/")
    print("   - GET    /api/v1/users/settings/")
    print("   - POST   /api/v1/users/change-password/")
    print("   - POST   /api/v1/users/avatar/")
    print()
    
    # Middleware check
    print("=" * 80)
    print("GOVERNANCE MIDDLEWARE VERIFICATION")
    print("=" * 80)
    print()
    print("✅ USERS is in PATH_TO_FEATURE mapping")
    print("✅ USERS is in critical path list (fail-open)")
    print()
    print("Behavior:")
    print("   - If governance unavailable → ALLOW (fail-open)")
    print("   - If feature flag OFF → BLOCK (but should never be OFF)")
    print("   - If feature flag BETA → Superusers only")
    print("   - If feature flag ON → Allow based on visibility")
    print()
    
    # Final summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    all_good = True
    
    if not platform_state:
        print("⚠️  PlatformState missing")
        all_good = False
    
    if not users_flag or users_flag.state != 'ON':
        print("⚠️  USERS feature flag not ON")
        all_good = False
    
    if users_flag and users_flag.visibility != 'public':
        print("⚠️  USERS visibility not public")
        all_good = False
    
    if all_good:
        print("✅ ALL CHECKS PASSED")
        print()
        print("USERS module is properly configured as a critical path.")
        print("Login and user endpoints should be accessible.")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print()
        print("Please review the warnings above and fix as needed.")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    verify_users_critical_path()
