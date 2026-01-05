def get_mentor_dashboard_stats(user):
    from appointments.models import Appointment

    return {
        "upcomingSessions": Appointment.objects.filter(
            mentor=user,
            status__in=["pending", "confirmed"],
        ).count(),
        "completedSessions": Appointment.objects.filter(
            mentor=user,
            status="completed",
        ).count(),
        "earningsThisMonth": 0,  # later connect payments
        "pendingRequests": 0,
    }
