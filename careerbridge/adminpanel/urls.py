from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # System statistics
    path('stats/', views.SystemStatsListView.as_view(), name='system-stats-list'),
    path('stats/<int:pk>/', views.SystemStatsDetailView.as_view(), name='system-stats-detail'),
    
    # Admin action logs
    path('actions/', views.AdminActionListView.as_view(), name='admin-action-list'),
    
    # System configuration
    path('config/', views.SystemConfigListView.as_view(), name='system-config-list'),
    path('config/<int:pk>/', views.SystemConfigDetailView.as_view(), name='system-config-detail'),
    
    # Data export
    path('exports/', views.DataExportListView.as_view(), name='data-export-list'),
    path('exports/<int:pk>/', views.DataExportDetailView.as_view(), name='data-export-detail'),
    path('exports/<int:pk>/download/', views.DataExportDownloadView.as_view(), name='data-export-download'),
    
    # Content moderation
    path('moderation/', views.ContentModerationListView.as_view(), name='content-moderation-list'),
    path('moderation/<int:pk>/', views.ContentModerationDetailView.as_view(), name='content-moderation-detail'),
    
    # User management
    path('users/', views.UserManagementView.as_view(), name='user-management'),
    path('users/search/', views.UserLookupView.as_view(), name='user-lookup'),
    
    # Mentor management
    path('mentors/', views.MentorManagementView.as_view(), name='mentor-management'),
    path('mentors/applications/', views.MentorApplicationsView.as_view(), name='mentor-applications'),
    path('mentors/applications/<int:application_id>/approve/', views.MentorApplicationApproveView.as_view(), name='mentor-application-approve'),
    path('mentors/applications/<int:application_id>/reject/', views.MentorApplicationRejectView.as_view(), name='mentor-application-reject'),
    
    # Appointments management
    path('appointments/', views.AppointmentManagementView.as_view(), name='appointment-management'),
    path('appointments/<int:pk>/', views.AppointmentManagementDetailView.as_view(), name='appointment-management-detail'),
    path('staff/appointments/', views.StaffAppointmentListView.as_view(), name='staff-appointment-list'),
    path('staff/appointments/<int:pk>/', views.StaffAppointmentDetailView.as_view(), name='staff-appointment-detail'),
    
    # Jobs management
    path('jobs/stats/', views.JobStatsView.as_view(), name='job-stats'),
    path('jobs/crawler/trigger/', views.JobCrawlerTriggerView.as_view(), name='job-crawler-trigger'),
    path('jobs/clean-expired/', views.JobCleanExpiredView.as_view(), name='job-clean-expired'),
    
    # Assessments management
    path('assessments/stats/', views.AssessmentStatsView.as_view(), name='assessment-stats'),
    path('assessments/', views.AssessmentListView.as_view(), name='assessment-list'),
    
    # Payouts management
    path('payouts/', views.PayoutListView.as_view(), name='payout-list'),
    path('payouts/<int:payout_id>/approve/', views.PayoutApproveView.as_view(), name='payout-approve'),
    path('payouts/<int:payout_id>/reject/', views.PayoutRejectView.as_view(), name='payout-reject'),
    
    # Content management
    path('content/', views.ContentListView.as_view(), name='content-list'),
    path('content/public/', views.ContentPublicListView.as_view(), name='content-public-list'),
    path('content/<int:content_id>/', views.ContentDetailView.as_view(), name='content-detail'),

    # Support tickets
    path('support/', views.SupportTicketListView.as_view(), name='support-ticket-list'),
    path('support/<int:pk>/', views.SupportTicketDetailView.as_view(), name='support-ticket-detail'),
    
    # Promotions management
    path('promotions/', views.PromotionListView.as_view(), name='promotion-list'),
    path('promotions/<int:promotion_id>/', views.PromotionDetailView.as_view(), name='promotion-detail'),
    
    # System configuration
    path('system/config/', views.SystemConfigView.as_view(), name='system-config'),
    path('system/cache/clear/', views.CacheClearView.as_view(), name='cache-clear'),
    
    # System settings (new comprehensive settings)
    path('system/settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    
    # Public system settings (no auth required)
    path('system/settings/public/', views.PublicSystemSettingsView.as_view(), name='public-system-settings'),
    
    # System actions
    path('system/actions/<str:action>/', views.SystemActionsView.as_view(), name='system-actions'),
    path('system/actions/error-logs/', views.ErrorLogsView.as_view(), name='error-logs'),
    
    # System health
    path('health/', views.SystemHealthView.as_view(), name='system-health'),
    
    # Ping endpoint for latency measurement
    path('ping/', views.PingView.as_view(), name='ping'),
]
