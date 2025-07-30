from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Time slot related
    path('time-slots/', views.TimeSlotListView.as_view(), name='time-slot-list'),
    path('time-slots/create/', views.TimeSlotCreateView.as_view(), name='time-slot-create'),
    path('time-slots/<int:pk>/', views.TimeSlotDetailView.as_view(), name='time-slot-detail'),
    
    # Appointment related
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Mentor appointment management
    path('mentor/appointments/', views.MentorAppointmentListView.as_view(), name='mentor-appointment-list'),
    
    # Appointment request related
    path('requests/', views.AppointmentRequestListView.as_view(), name='appointment-request-list'),
    path('requests/<int:pk>/', views.AppointmentRequestDetailView.as_view(), name='appointment-request-detail'),
    
    # Statistics
    path('stats/', views.AppointmentStatsView.as_view(), name='appointment-stats'),
]