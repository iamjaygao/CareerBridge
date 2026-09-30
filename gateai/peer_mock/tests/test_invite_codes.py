"""Invite codes: only hashes are stored; the command prints each plaintext once."""

import io
from datetime import timedelta

from django.core.management import CommandError, call_command
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from peer_mock import invites
from peer_mock.models import InviteCode


class InviteCodeTest(TestCase):

    def test_only_the_hash_is_stored(self):
        invite, code = invites.create('cohort-1', 5)
        self.assertRegex(code, r'^[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$')
        self.assertEqual(invite.code_hash, invites.hash_code(code))
        stored = InviteCode.objects.filter(pk=invite.pk).values().get()
        self.assertNotIn(code, str(stored))
        self.assertNotIn(invites.normalise(code), str(stored))

    def test_consume_respects_max_uses_and_expiry(self):
        invite, code = invites.create('two', 2)
        with transaction.atomic():
            self.assertEqual(invites.consume(code), invite)
            self.assertEqual(invites.consume(code.lower()), invite)
            self.assertIsNone(invites.consume(code))
        _, old = invites.create('old', 5, expires_at=timezone.now() - timedelta(minutes=1))
        with transaction.atomic():
            self.assertIsNone(invites.consume(old))
            self.assertIsNone(invites.consume(''))


class InviteCodeCommandTest(TestCase):

    def call(self, *args):
        out, err = io.StringIO(), io.StringIO()
        call_command('peer_invite_codes', *args, stdout=out, stderr=err)
        return out.getvalue()

    def test_create_list_disable(self):
        printed = self.call('create', '--label', 'group A', '--max-uses', '3', '--count', '2').splitlines()
        self.assertEqual(len(printed), 2)
        codes = [line.split('\t')[0] for line in printed]
        self.assertEqual({invites.hash_code(c) for c in codes},
                         set(InviteCode.objects.values_list('code_hash', flat=True)))
        listing = self.call('list')
        self.assertIn('group A\t0/3', listing)
        self.assertNotIn(codes[0], listing)  # plaintext is shown only at creation
        self.assertIn('disabled 2 code(s)', self.call('disable', '--label', 'group A'))
        self.assertFalse(InviteCode.objects.filter(active=True).exists())
        with self.assertRaises(CommandError):
            self.call('disable', '--label', 'group A')
        with self.assertRaises(CommandError):
            self.call('create', '--label', 'x', '--max-uses', '0')
