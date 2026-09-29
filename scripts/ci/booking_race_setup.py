# Runs inside the app container: python manage.py shell < booking_race_setup.py
# Prepares a mentor, ROUNDS free slots and USERS users; prints one JSON line.
import json
import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from appointments.models import TimeSlot
from human_loop.models import MentorProfile, MentorService
from kernel.governance.models import BusPowerState, PlatformState

USERS = int(os.environ.get("RACE_USERS", "10"))
ROUNDS = int(os.environ.get("RACE_ROUNDS", "10"))

if not PlatformState.objects.exists():
    call_command("kernel_init_governance", verbosity=0)
# decision-slots (booking) lives on AI_BUS; power it for the test only.
BusPowerState.objects.update_or_create(bus_name="AI_BUS", defaults={"state": "ON"})

User = get_user_model()
stamp = timezone.now().strftime("%Y%m%d%H%M%S")
mentor_user = User.objects.create_user(username=f"race_mentor_{stamp}", email=f"race_mentor_{stamp}@example.com", password=None)
mentor = MentorProfile.objects.create(user=mentor_user, bio="bio", current_position="Engineer", industry="Tech")
service = MentorService.objects.create(mentor=mentor, service_type="mock_interview", title="Mock",
                                       description="Mock interview", duration_minutes=60)
start = timezone.now().replace(microsecond=0) + timedelta(days=30)
slots = [TimeSlot.objects.create(mentor=mentor, start_time=start + timedelta(days=i),
                                 end_time=start + timedelta(days=i, hours=2), price=Decimal("50.00")).id
         for i in range(ROUNDS)]
tokens = []
for i in range(USERS):
    u = User.objects.create_user(username=f"racer_{stamp}_{i}", email=f"racer_{stamp}_{i}@example.com", password=None)
    tokens.append(str(RefreshToken.for_user(u).access_token))
print("RACE_SETUP " + json.dumps({"service_id": service.id, "slots": slots, "tokens": tokens}))
