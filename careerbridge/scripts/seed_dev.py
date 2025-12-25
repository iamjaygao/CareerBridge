# scripts/seed_dev.py
import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careerbridge.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from mentors.models import MentorProfile, MentorService

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
    if not settings.DEBUG:
        raise RuntimeError("❌ seed_dev 只能在 DEBUG 模式运行")

    seed_system_users()
    seed_mentors(20)

    print("🎉 seed_dev 完成（完全匹配当前 DB）")


run()
