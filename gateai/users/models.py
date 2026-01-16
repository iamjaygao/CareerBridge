"""
GateAI Kernel IAM User Models

KERNEL IAM COMPLIANCE:
This module defines GateAI's single sovereign identity universe.
The User model extends Django's AbstractUser (Kernel IAM), ensuring
all authentication flows through the kernel.

NO parallel user universe exists.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class AdminCapability(models.Model):
    """
    Capability-based permissions for userland admins (is_staff).
    Enables fine-grained duty separation within /admin.
    """
    code = models.CharField(max_length=64, unique=True)   # e.g. 'mock.manage'
    description = models.TextField()

    def __str__(self):
        return f"{self.code} - {self.description[:30]}"

    class Meta:
        verbose_name = "Admin Capability"
        verbose_name_plural = "Admin Capabilities"


class User(AbstractUser):
    """
    GateAI Kernel IAM User Model (Single Identity Universe)
    
    This IS the Django Kernel IAM user - NOT a separate business table.
    Extends AbstractUser to inherit Django's authentication system:
    
    INHERITED FROM AbstractUser (Kernel IAM):
    ────────────────────────────────────────────────────────────────
    - username          (CharField, unique)
    - password          (CharField, hashed with Django hashers)
    - email             (EmailField)
    - is_superuser      (BooleanField) ← KERNEL GATE FLAG
    - is_staff          (BooleanField) ← ADMIN GATE FLAG
    - is_active         (BooleanField)
    - date_joined       (DateTimeField)
    - first_name        (CharField)
    - last_name         (CharField)
    - Django permission system
    - Django password hashing (PBKDF2)
    
    DATABASE TABLE: users_user
    ────────────────────────────────────────────────────────────────
    NOTE: The table is named `users_user` (not `auth_user`) because
    AUTH_USER_MODEL = 'users.User', but this IS still Kernel IAM.
    Table name doesn't matter - architecture does.
    
    NO PARALLEL USER UNIVERSE EXISTS.
    ────────────────────────────────────────────────────────────────
    All authentication, authorization, and token generation flows
    through this model via Django's get_user_model().
    
    BUSINESS FIELDS:
    ────────────────────────────────────────────────────────────────
    The fields below extend the kernel user with business logic.
    They do NOT create a parallel authentication system.
    """
    
    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
        ('staff', 'Staff'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    username_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Password reset fields
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    location = models.CharField(max_length=128, null=True, blank=True)

    # Capability-based roles (Userland Admin World)
    capabilities = models.ManyToManyField(AdminCapability, blank=True, related_name='users')

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def has_capability(self, cap_code):
        """Helper to check if user has a specific admin capability"""
        if self.is_superuser:
            return True  # Superusers have all capabilities by default
        return self.capabilities.filter(code=cap_code).exists()

    def save(self, *args, **kwargs):
        """
        Kernel IAM Flag Synchronization
        
        Ensures Django authentication flags (is_superuser, is_staff) stay
        in sync with the business role field. This maintains consistency
        between kernel-level permissions and application-level roles.
        
        PRIORITY: Django flags (is_superuser, is_staff) are source of truth.
        The role field is derived/synced from these flags.
        """
        # 1. 如果是超级用户，强制设定角色
        if self.is_superuser:
            self.role = 'superadmin'
        
        # 2. 如果是工作人员 (is_staff) 且角色还是默认的 student，
        # 自动提升为 admin (或者你认为合适的默认管理角色)
        elif self.is_staff and self.role == 'student':
            self.role = 'admin'

        # 3. 如果角色是 superadmin 但没勾选 is_superuser，
        # 反向同步确保权限生效
        if self.role == 'superadmin':
            self.is_superuser = True
            self.is_staff = True
        elif self.role == 'admin' or self.role == 'staff':
            self.is_staff = True

        super().save(*args, **kwargs)


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.username}"


# Create your models here.
