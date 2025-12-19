from django.urls import path

from dashboard.views.student import StudentDashboardView
from dashboard.views.mentor import MentorDashboardView
from dashboard.views.staff import StaffDashboardView
from dashboard.views.admin import AdminDashboardView
from dashboard.views.superadmin import SuperAdminDashboardView

urlpatterns = [
    path("student/", StudentDashboardView.as_view()),
    path("mentor/", MentorDashboardView.as_view()),
    path("staff/", StaffDashboardView.as_view()),
    path("admin/", AdminDashboardView.as_view()),
    path("superadmin/", SuperAdminDashboardView.as_view()),
]
