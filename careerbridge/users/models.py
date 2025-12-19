from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
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

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def save(self, *args, **kwargs):
        """
        重写 save 方法，确保权限位 (is_superuser/is_staff) 
        与业务角色 (role) 始终保持同步。
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


# Create your models here.
