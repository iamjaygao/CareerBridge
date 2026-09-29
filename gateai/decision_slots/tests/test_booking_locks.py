"""
Booking flows go through sys_claim (sequential; SQLite and Postgres).

Every create/reschedule claims a TIME_SLOT ResourceLock for the slot, owned by
the booking user; cancel releases it. A slot held or booked by someone else is
never overwritten (409).
"""

from datetime import timedelta

from django.test import TransactionTestCase
from django.utils import timezone

from appointments.models import Appointment, TimeSlot
from decision_slots.models import ResourceLock
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
from kernel.policies.bus_power import invalidate_cache

from .booking_fixtures import (book, cancel, client_for, make_mentor, make_slot, make_user,
                               power_booking_buses, reschedule)


def slot_lock(slot):
    return ResourceLock.objects.filter(resource_type=ResourceLock.RESOURCE_TYPE_TIME_SLOT,
                                       resource_id=slot.id, status='active').first()


class BookingLockTest(TransactionTestCase):

    def setUp(self):
        power_booking_buses()
        self.addCleanup(invalidate_cache)
        self.mentor, self.service = make_mentor()
        self.slot_a, self.slot_b, self.slot_c = (make_slot(self.mentor, d) for d in (1, 2, 3))
        self.alice, self.bob = make_user('alice'), make_user('bob')
        self.ca, self.cb = client_for(self.alice), client_for(self.bob)

    def tearDown(self):
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()

    def test_create_claims_slot_lock_for_the_user(self):
        response = book(self.ca, self.slot_a, self.service)
        self.assertEqual(response.status_code, 201, response.content)
        lock = slot_lock(self.slot_a)
        self.assertIsNotNone(lock, 'create must go through sys_claim')
        self.assertEqual(lock.owner_id, self.alice.id)

    def test_create_on_held_slot_by_other_user_is_409(self):
        self.assertEqual(book(self.ca, self.slot_a, self.service).status_code, 201)
        self.assertEqual(book(self.cb, self.slot_a, self.service).status_code, 409)
        self.assertEqual(slot_lock(self.slot_a).owner_id, self.alice.id)

    def test_same_user_create_retry_is_idempotent(self):
        first = book(self.ca, self.slot_a, self.service)
        again = book(self.ca, self.slot_a, self.service)
        self.assertEqual(again.status_code, 200, again.content)
        self.assertEqual(again.json()['appointment']['id'], first.json()['appointment']['id'])
        self.assertEqual(ResourceLock.objects.filter(resource_id=self.slot_a.id, status='active').count(), 1)

    def test_reschedule_onto_slot_held_by_other_user_is_409(self):
        mine = book(self.ca, self.slot_a, self.service).json()['appointment']['id']
        theirs = book(self.cb, self.slot_b, self.service).json()['appointment']['id']
        response = reschedule(self.ca, mine, self.slot_b, self.service)
        self.assertEqual(response.status_code, 409, response.content)
        # Bob's hold is intact, Alice stays where she was.
        self.assertEqual(TimeSlot.objects.get(pk=self.slot_b.pk).reserved_appointment_id, theirs)
        self.assertEqual(Appointment.objects.get(pk=mine).time_slot_id, self.slot_a.id)
        self.assertEqual(slot_lock(self.slot_b).owner_id, self.bob.id)
        self.assertEqual(slot_lock(self.slot_a).owner_id, self.alice.id)

    def test_reschedule_onto_booked_slot_is_409(self):
        mine = book(self.ca, self.slot_a, self.service).json()['appointment']['id']
        theirs = book(self.cb, self.slot_b, self.service).json()['appointment']['id']
        Appointment.objects.filter(pk=theirs).update(status='confirmed', is_paid=True)
        TimeSlot.objects.filter(pk=self.slot_b.pk).update(reserved_until=None, is_available=False)
        response = reschedule(self.ca, mine, self.slot_b, self.service)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(TimeSlot.objects.get(pk=self.slot_b.pk).reserved_appointment_id, theirs)

    def test_reschedule_onto_free_slot_moves_the_lock(self):
        mine = book(self.ca, self.slot_a, self.service).json()['appointment']['id']
        response = reschedule(self.ca, mine, self.slot_c, self.service)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(slot_lock(self.slot_c).owner_id, self.alice.id)
        self.assertIsNone(slot_lock(self.slot_a), 'old slot lock must be released')
        # The freed slot can now be booked by someone else.
        self.assertEqual(book(self.cb, self.slot_a, self.service).status_code, 201)

    def test_cancel_releases_the_lock(self):
        mine = book(self.ca, self.slot_a, self.service).json()['appointment']['id']
        self.assertEqual(cancel(self.ca, mine).status_code, 200)
        self.assertIsNone(slot_lock(self.slot_a))
        self.assertEqual(book(self.cb, self.slot_a, self.service).status_code, 201)

    def test_expired_hold_is_taken_over(self):
        book(self.cb, self.slot_a, self.service)
        past = timezone.now() - timedelta(minutes=1)
        TimeSlot.objects.filter(pk=self.slot_a.pk).update(reserved_until=past)
        ResourceLock.objects.filter(resource_id=self.slot_a.id).update(expires_at=past)
        response = book(self.ca, self.slot_a, self.service)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(slot_lock(self.slot_a).owner_id, self.alice.id)
