from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    
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
    
    # Content moderation
    path('moderation/', views.ContentModerationListView.as_view(), name='content-moderation-list'),
    path('moderation/<int:pk>/', views.ContentModerationDetailView.as_view(), name='content-moderation-detail'),
    
    # User management
    path('users/', views.UserManagementView.as_view(), name='user-management'),
    
    # Mentor management
    path('mentors/', views.MentorManagementView.as_view(), name='mentor-management'),
    path('mentors/applications/', views.MentorApplicationsView.as_view(), name='mentor-applications'),
    
    # System health
    path('health/', views.SystemHealthView.as_view(), name='system-health'),
]