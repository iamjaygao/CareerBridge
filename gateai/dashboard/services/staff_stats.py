from django.contrib.auth import get_user_model

User = get_user_model()


def get_staff_dashboard_stats():
    return {
        "newUsersToday": 0,
        "pendingMentorReviews": 0,
        "reportedIssues": 0,
    }
