def get_student_dashboard_stats(user):
    from decision_slots.models import Appointment
    from ats_signals.models import Resume

    return {
        "upcomingAppointments": Appointment.objects.filter(
            user=user,
            status__in=["pending", "confirmed"],
        ).count(),
        "mentorSessions": Appointment.objects.filter(
            user=user,
            status="completed",
        ).count(),
        "resumesUploaded": Resume.objects.filter(user=user).count(),
        "profileViews": 0,
    }
