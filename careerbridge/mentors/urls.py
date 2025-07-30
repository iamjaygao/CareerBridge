from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for nested resources
router = DefaultRouter()

app_name = 'mentors'

urlpatterns = [
    # Mentor listing and discovery
    path('', views.MentorListView.as_view(), name='mentor-list'),
    path('search/', views.MentorSearchView.as_view(), name='mentor-search'),
    path('recommendations/', views.MentorRecommendationView.as_view(), name='mentor-recommendations'),
    path('rankings/', views.MentorRankingView.as_view(), name='mentor-rankings'),
    
    # Individual mentor details
    path('<int:pk>/', views.MentorDetailView.as_view(), name='mentor-detail'),
    path('<int:mentor_id>/services/', views.MentorServiceView.as_view(), name='mentor-services'),
    path('<int:mentor_id>/availability/', views.MentorAvailabilityView.as_view(), name='mentor-availability'),
    path('<int:mentor_id>/availability/slots/', views.MentorAvailabilitySlotsView.as_view(), name='mentor-availability-slots'),
    path('<int:mentor_id>/reviews/', views.MentorReviewView.as_view(), name='mentor-reviews'),
    path('<int:mentor_id>/analytics/', views.MentorAnalyticsView.as_view(), name='mentor-analytics'),
    
    # Sessions (appointments)
    path('sessions/', views.MentorSessionView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.MentorSessionDetailView.as_view(), name='session-detail'),
    
    # Applications
    path('apply/', views.MentorApplicationView.as_view(), name='mentor-apply'),
    path('application/status/', views.MentorApplicationStatusView.as_view(), name='application-status'),
    
    # Payments
    path('payments/', views.MentorPaymentView.as_view(), name='payment-list'),
    
    # Notifications
    path('notifications/', views.MentorNotificationView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.MentorNotificationDetailView.as_view(), name='notification-detail'),
    
    # Platform analytics (admin only)
    path('analytics/platform/', views.PlatformAnalyticsView.as_view(), name='platform-analytics'),
    
    # Mentor profile management (for mentors only)
    path('profile/update/', views.MentorProfileUpdateView.as_view(), name='mentor-profile-update'),
    path('services/<int:pk>/update/', views.MentorServiceUpdateView.as_view(), name='mentor-service-update'),
    path('availability/<int:pk>/update/', views.MentorAvailabilityUpdateView.as_view(), name='mentor-availability-update'),
]