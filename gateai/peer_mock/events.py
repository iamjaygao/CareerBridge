"""Write PeerEvent rows in the caller's transaction (design doc §6.1)."""

from django.db import IntegrityError, transaction

from .models import PeerEvent, PeerProfile


def emit(event_type, *, user=None, actor_kind='user', round_id=None, session_id=None, metadata=None,
         idempotency_key=None):
    """
    Record one event. Call inside the same transaction as the state change.

    With an idempotency_key, a duplicate is silently ignored (returns None).
    Metadata must not contain PII.
    """
    actor_ref = None
    if user is not None:
        actor_ref = PeerProfile.objects.filter(user=user).values_list('actor_ref', flat=True).first()
    fields = dict(event_type=event_type, user=user, actor_ref=actor_ref, actor_kind=actor_kind,
                  round_id=round_id, session_id=session_id, metadata=metadata or {},
                  idempotency_key=idempotency_key)
    if idempotency_key is None:
        return PeerEvent.objects.create(**fields)
    try:
        with transaction.atomic():  # savepoint: a duplicate must not break the caller's transaction
            return PeerEvent.objects.create(**fields)
    except IntegrityError:
        return None


def attach_actor_ref(profile):
    """Give events recorded before onboarding (signup, email_verified) the new actor_ref."""
    PeerEvent.objects.filter(user=profile.user, actor_ref__isnull=True).update(actor_ref=profile.actor_ref)
