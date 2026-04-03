"""
Kernel Admin Registration

Registers kernel models in Django admin.
"""

from django.contrib import admin

# Register governance admin
from kernel.governance.admin import PlatformStateAdmin, FeatureFlagAdmin, GovernanceAuditAdmin

# Note: Models are already registered via @admin.register decorators in governance/admin.py
# This import ensures they are loaded when admin is initialized
