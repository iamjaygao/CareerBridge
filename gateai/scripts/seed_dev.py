# scripts/seed_dev.py
import os
import sys
import django
import random


def _production_reason(settings=None):
    """Return why this looks like production, or None if it looks like dev."""
    if os.environ.get("DJANGO_ENV", "").lower() == "production":
        return "DJANGO_ENV=production"
    if os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith("settings_prod"):
        return "DJANGO_SETTINGS_MODULE is settings_prod"
    if settings is not None and not settings.DEBUG:
        return "DEBUG is off"
    return None


def _refuse_if_production(settings=None):
    reason = _production_reason(settings)
    if reason:
        sys.exit(f"❌ seed_dev refused: this looks like production ({reason}). Dev only.")


# Check the environment before Django (and the database) is touched at all.
_refuse_if_production()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gateai.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from human_loop.models import MentorProfile, MentorService

User = get_user_model()

# -------------------------
# 基础配置
# -------------------------
DEFAULT_PASSWORD = "123456789"

MENTOR_TITLES = [
    "Senior Backend Engineer",
    "Staff Software Engineer",
    "Principal Engineer",
    "Senior Frontend Engineer",
    "Full Stack Lead",
    "System Architect",
    "Data Scientist",
    "Machine Learning Engineer",
    "Product Manager",
    "Engineering Manager",
]

INDUSTRIES = [
    "Technology",
    "Data",
    "Product",
    "AI",
    "Finance",
]

SERVICE_TYPES = [
    ("resume_review", "Resume Review"),
    ("mock_interview", "Mock Interview"),
]

# -------------------------
# 创建系统测试用户
# -------------------------
def seed_system_users():
    print("👤 创建系统用户...")

    users = [
        ("admin", "admin", True, True),
        ("staff", "staff", True, False),
        ("test_mentor", "mentor", False, False),
        ("student", "student", False, False),
    ]

    for username, role, is_staff, is_superuser in users:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@test.local",
                "role": role,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            print(f"✅ created user: {username}")
        else:
            print(f"⚠️ user exists: {username}")


# -------------------------
# 创建导师 + 服务
# -------------------------
def seed_mentors(count=20):
    print(f"🧑‍🏫 创建 {count} 个导师...")

    for i in range(1, count + 1):
        username = f"mentor{i}"

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@test.local",
                "role": "mentor",
            },
        )

        user.set_password(DEFAULT_PASSWORD)
        user.role = "mentor"
        user.save()

        profile, created = MentorProfile.objects.get_or_create(
            user=user,
            defaults={
                "bio": f"{random.choice(MENTOR_TITLES)} with 8+ years experience",
                "years_of_experience": random.randint(3, 15),
                "current_position": random.choice(MENTOR_TITLES),
                "industry": random.choice(INDUSTRIES),
                "status": "approved",
                "is_verified": True,
                "verification_badge": "verified",
                "specializations": ["Interview", "Career", "System Design"],
            },
        )

        if created:
            print(f"🧑‍🏫 mentor profile created: {username}")

        # 每个 mentor 1–2 个服务
        for stype, title in random.sample(SERVICE_TYPES, k=random.randint(1, 2)):
            MentorService.objects.get_or_create(
                mentor=profile,
                service_type=stype,
                defaults={
                    "title": title,
                    "price_per_hour": random.randint(50, 200),
                    "duration_minutes": random.choice([30, 60]),
                },
            )


# -------------------------
# 主入口
# -------------------------
def run():
    # Re-check with the loaded settings (catches DEBUG off, and prod settings
    # selected indirectly, e.g. via gateai.settings + DJANGO_ENV).
    _refuse_if_production(settings)

    seed_system_users()
    seed_mentors(20)

    print("🎉 seed_dev 完成（完全匹配当前 DB）")


run()
