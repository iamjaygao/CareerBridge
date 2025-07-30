from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User notification endpoints
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('stats/', views.NotificationStatsView.as_view(), name='notification-stats'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('<int:pk>/delete/', views.NotificationDeleteView.as_view(), name='notification-delete'),
    path('delete-all/', views.NotificationDeleteAllView.as_view(), name='notification-delete-all'),
    
    # Admin functionality
    path('create/', views.NotificationCreateView.as_view(), name='notification-create'),
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification-template-list'),
    path('templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='notification-template-detail'),
    path('logs/', views.NotificationLogListView.as_view(), name='notification-log-list'),
    path('batches/', views.NotificationBatchListView.as_view(), name='notification-batch-list'),
    path('batches/<int:pk>/', views.NotificationBatchDetailView.as_view(), name='notification-batch-detail'),
]