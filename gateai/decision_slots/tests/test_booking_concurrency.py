"""
Real concurrency tests for booking and rescheduling (PostgreSQL).

N users hit lock_slot at the same instant (barrier, one DB connection per
thread); exactly one may get the slot. Repeated ITERATIONS times (default 100).
"""

from collections import Counter

from django.test import TransactionTestCase

from appointments.models import Appointment, TimeSlot
from decision_slots.models import ResourceLock
from kernel.models import KernelAuditLog, KernelIdempotencyRecord
from kernel.policies.bus_power import invalidate_cache
from kernel.tests.concurrency import ITERATIONS, requires_postgres, run_concurrently

from .booking_fixtures import book, client_for, make_mentor, make_slot, make_user, power_booking_buses, reschedule

N = 5


@requires_postgres
class BookingConcurrencyTest(TransactionTestCase):

    def setUp(self):
        power_booking_buses()
        self.addCleanup(invalidate_cache)
        self.mentor, self.service = make_mentor()
        self.users = [make_user(f'u{i}') for i in range(N)]

    def tearDown(self):
        ResourceLock.objects.all().delete()
        KernelAuditLog.objects.all().delete()
        KernelIdempotencyRecord.objects.all().delete()

    def slot_lock_owner(self, slot):
        locks = ResourceLock.objects.filter(resource_type=ResourceLock.RESOURCE_TYPE_TIME_SLOT,
                                            resource_id=slot.id, status='active')
        self.assertEqual(locks.count(), 1)
        return locks.get().owner_id

    def test_concurrent_create_on_same_slot(self):
        for it in range(ITERATIONS):
            slot = make_slot(self.mentor, day_offset=10 + it)
            codes = run_concurrently(N, lambda i: book(client_for(self.users[i]), slot, self.service).status_code)
            self.assertEqual(Counter(codes), Counter({201: 1, 409: N - 1}), f'iteration {it}')
            winner = self.users[codes.index(201)]
            self.assertEqual(self.slot_lock_owner(slot), winner.id)
            self.assertEqual(Appointment.objects.filter(time_slot=slot, status='pending').count(), 1)

    def test_concurrent_reschedule_into_same_free_slot(self):
        for it in range(ITERATIONS):
            own_slots = [make_slot(self.mentor, day_offset=200 + it * (N + 1) + i) for i in range(N)]
            target = make_slot(self.mentor, day_offset=200 + it * (N + 1) + N)
            appts = [book(client_for(u), s, self.service).json()['appointment']['id']
                     for u, s in zip(self.users, own_slots)]
            codes = run_concurrently(
                N, lambda i: reschedule(client_for(self.users[i]), appts[i], target, self.service).status_code)
            self.assertEqual(Counter(codes), Counter({200: 1, 409: N - 1}), f'iteration {it}')
            w = codes.index(200)
            self.assertEqual(self.slot_lock_owner(target), self.users[w].id)
            self.assertEqual(TimeSlot.objects.get(pk=target.pk).reserved_appointment_id, appts[w])
            for i in range(N):
                if i != w:  # losers keep their own slot and lock
                    self.assertEqual(Appointment.objects.get(pk=appts[i]).time_slot_id, own_slots[i].id)
                    self.assertEqual(self.slot_lock_owner(own_slots[i]), self.users[i].id)

    def test_create_races_reschedule_for_same_slot(self):
        mover, creator = self.users[0], self.users[1]
        for it in range(ITERATIONS):
            home = make_slot(self.mentor, day_offset=1000 + 2 * it)
            target = make_slot(self.mentor, day_offset=1001 + 2 * it)
            appt = book(client_for(mover), home, self.service).json()['appointment']['id']

            def act(i):
                if i == 0:
                    return reschedule(client_for(mover), appt, target, self.service).status_code
                return book(client_for(creator), target, self.service).status_code

            codes = run_concurrently(2, act)
            # Exactly one of (reschedule -> 200, create -> 201) succeeds; the other is 409.
            self.assertIn(codes, ([200, 409], [409, 201]), f'iteration {it}: {codes}')
            self.assertEqual(Appointment.objects.filter(time_slot=target).exclude(status='expired').count(), 1)
