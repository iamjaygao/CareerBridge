from django.urls import path
from . import views

app_name = 'decision_slots'

urlpatterns = [
    # === KERNEL ARBITRATION ENDPOINTS ONLY ===
    # Time slot related (kernel resource management)
    path('time-slots/', views.TimeSlotListView.as_view(), name='time-slot-list'),
    path('time-slots/create/', views.TimeSlotCreateView.as_view(), name='time-slot-create'),
    path('time-slots/<int:pk>/', views.TimeSlotDetailView.as_view(), name='time-slot-detail'),
    
    # Slot locking (kernel arbitration)
    path('lock-slot/', views.lock_slot, name='lock-slot'),
    path(
        'lock-status/<int:appointment_id>/',
        views.appointment_lock_status,
        name='appointment-lock-status'
    ),

    # === DEPRECATED: Appointment domain routes REMOVED ===
    # All appointment CRUD operations have been moved to appointments app
    # See /api/v1/appointments/ for appointment management
]
