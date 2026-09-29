"""Shared fixtures for booking/lock tests (mentor, service, slots, clients)."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from appointments.models import TimeSlot
from human_loop.models import MentorProfile, MentorService
from kernel.governance.models import BusPowerState, PlatformState
from kernel.policies.bus_power import BUS_POWER_DEFAULTS, invalidate_cache

LOCK_SLOT_URL = '/api/v1/decision-slots/lock-slot/'
User = get_user_model()


def power_booking_buses():
    """decision-slots lives on AI_BUS; initialise governance so it isn't fail-closed."""
    BusPowerState.objects.all().delete()
    BusPowerState.objects.bulk_create([
        BusPowerState(bus_name=n, state=s) for n, s in {**BUS_POWER_DEFAULTS, 'AI_BUS': 'ON'}.items()
    ])
    invalidate_cache()
    if not PlatformState.objects.exists():
        PlatformState.objects.create(state='SINGLE_WORKLOAD', active_workloads=[], frozen_modules=[], reason='t')


def make_user(name):
    return User.objects.create_user(username=name, email=f'{name}@example.com', password='pw')


def make_mentor(name='mentor'):
    user = make_user(name)
    profile = MentorProfile.objects.create(user=user, bio='bio', current_position='Engineer', industry='Tech')
    service = MentorService.objects.create(mentor=profile, service_type='mock_interview', title='Mock',
                                           description='Mock interview', duration_minutes=60)
    return profile, service


def make_slot(mentor, day_offset=1):
    start = timezone.now().replace(microsecond=0) + timedelta(days=day_offset)
    return TimeSlot.objects.create(mentor=mentor, start_time=start, end_time=start + timedelta(hours=2),
                                   price=Decimal('50.00'))


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')
    return client


def book(client, slot, service):
    return client.post(LOCK_SLOT_URL, {'time_slot_id': slot.id, 'service_id': service.id}, format='json')


def reschedule(client, appointment_id, slot, service):
    return client.post(LOCK_SLOT_URL, {'appointment_id': appointment_id, 'time_slot_id': slot.id,
                                       'service_id': service.id}, format='json')


def cancel(client, appointment_id):
    return client.post(LOCK_SLOT_URL, {'appointment_id': appointment_id, 'action': 'cancel'}, format='json')
