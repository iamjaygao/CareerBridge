"""Record signup and email verification of users (event log, design doc §6.1)."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from .events import emit

User = get_user_model()


@receiver(post_init, sender=User)
def remember_verification_state(sender, instance, **kwargs):
    instance._peer_email_verified_initial = instance.email_verified


@receiver(post_save, sender=User)
def record_user_events(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    if created:
        emit('signup', user=instance, actor_kind='system')
    elif instance.email_verified and not getattr(instance, '_peer_email_verified_initial', True):
        emit('email_verified', user=instance, actor_kind='system',
             idempotency_key=f'email_verified:{instance.pk}')
    instance._peer_email_verified_initial = instance.email_verified
