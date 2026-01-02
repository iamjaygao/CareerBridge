from django.contrib.auth import get_user_model

User = get_user_model()


def get_admin_dashboard_stats():
    return {
        "totalUsers": User.objects.count(),
        "activeUsers": User.objects.filter(is_active=True).count(),
    }
