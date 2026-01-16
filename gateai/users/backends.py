"""
GateAI Authentication Backend (Kernel IAM)

KERNEL IAM COMPLIANCE:
This backend enhances Django's ModelBackend to allow email OR username login,
but still authenticates against the SAME Kernel IAM user table.

NO parallel authentication system exists.
"""

from __future__ import annotations

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()  # ✅ Always returns Kernel IAM user


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with email OR username.

    KERNEL IAM COMPLIANCE:
    - Uses get_user_model() to fetch Kernel IAM users
    - Extends Django's ModelBackend
    - Uses Django's password verification (check_password)
    - NO parallel authentication system
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Django calls authenticate() with (request, username, password, **kwargs)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
