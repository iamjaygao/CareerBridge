"""Invite codes: generation, normalisation and single-use consumption (design doc §1.1)."""

import hashlib
import secrets

from django.db.models import Q
from django.utils import timezone

from .models import InviteCode

# No 0/O/1/I, so codes read back reliably. 12 characters ≈ 60 bits.
ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
LENGTH = 12


def normalise(code):
    return ''.join(ch for ch in str(code).upper() if ch not in '- \t')


def hash_code(code):
    return hashlib.sha256(normalise(code).encode()).hexdigest()


def generate():
    raw = ''.join(secrets.choice(ALPHABET) for _ in range(LENGTH))
    return '-'.join(raw[i:i + 4] for i in range(0, LENGTH, 4))


def create(label, max_uses, expires_at=None):
    """Create a code; returns (InviteCode, plaintext). The plaintext is never stored."""
    code = generate()
    invite = InviteCode.objects.create(code_hash=hash_code(code), label=label, max_uses=max_uses,
                                       expires_at=expires_at)
    return invite, code


def consume(code, now=None):
    """
    Use one slot of a valid code; returns the InviteCode or None.

    Must run inside a transaction: the row is locked, so concurrent callers
    cannot use more than max_uses slots.
    """
    if not code:
        return None
    now = now or timezone.now()
    invite = (InviteCode.objects.select_for_update()
              .filter(code_hash=hash_code(code), active=True)
              .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
              .first())
    if invite is None or invite.uses >= invite.max_uses:
        return None
    invite.uses += 1
    invite.save(update_fields=['uses'])
    return invite
