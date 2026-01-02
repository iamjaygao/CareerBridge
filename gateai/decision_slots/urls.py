from django.urls import path
from . import views

app_name = 'decision_slots'  # Backward compatibility: old name 'appointments' still works via URL redirect

urlpatterns = [
    # Time slot related
    path('time-slots/', views.TimeSlotListView.as_view(), name='time-slot-list'),
    path('time-slots/create/', views.TimeSlotCreateView.as_view(), name='time-slot-create'),
    path('time-slots/<int:pk>/', views.TimeSlotDetailView.as_view(), name='time-slot-detail'),
    
    # Appointment related
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<int:pk>/cancel/', views.AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('appointments/<int:pk>/rate/', views.AppointmentRateView.as_view(), name='appointment-rate'),
    
    # Mentor appointment management
    path('mentor/appointments/', views.MentorAppointmentListView.as_view(), name='mentor-appointment-list'),
    path('mentor/appointments/<int:pk>/status/', views.MentorAppointmentStatusView.as_view(), name='mentor-appointment-status'),
    
    # Appointment request related
    path('requests/', views.AppointmentRequestListView.as_view(), name='appointment-request-list'),
    path('requests/<int:pk>/', views.AppointmentRequestDetailView.as_view(), name='appointment-request-detail'),
    path('requests/<int:pk>/respond/', views.appointment_request_respond, name='appointment-request-respond'),
    
    # Statistics
    path('stats/', views.AppointmentStatsView.as_view(), name='appointment-stats'),
    
    # Slot locking
    path('lock-slot/', views.lock_slot, name='lock-slot'),
    path(
        'lock-status/<int:appointment_id>/',
        views.appointment_lock_status,
        name='appointment-lock-status'
    ),

]
