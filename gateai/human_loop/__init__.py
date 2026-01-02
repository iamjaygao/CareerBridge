"""
Human Loop app - GateAI OS Kernel module for human-in-the-loop workflows.

This module handles:
- Human review tasks for critical ATS signals
- Mentor profiles and services
- Review workflows
"""

# DO NOT import models/views/serializers here at module level.
# Django apps must not import ORM models in __init__.py to avoid AppRegistryNotReady errors.
# Import these modules directly where needed: from human_loop.models import ...
