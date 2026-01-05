"""
DEPRECATED: decision_slots/serializers.py

Serializers moved to appointments.serializers as of Day 1 isolation work.
This module maintained for backward compatibility during transition.

To be removed in Day 4+ cleanup phase.
"""

# Backward-compatible re-export
from appointments.serializers import (  # noqa: F401
    TimeSlotSerializer,
    AppointmentSerializer,
    AppointmentRequestSerializer,
    AppointmentUpdateSerializer,
    TimeSlotCreateSerializer,
)

__all__ = [
    'TimeSlotSerializer',
    'AppointmentSerializer',
    'AppointmentRequestSerializer',
    'AppointmentUpdateSerializer',
    'TimeSlotCreateSerializer',
]
