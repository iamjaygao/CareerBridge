from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length = 10, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# Create your models here.
