"""
Manage peer mock invite codes.

    manage.py peer_invite_codes create --label "group A" --max-uses 50 [--expires-days 30] [--count 1]
    manage.py peer_invite_codes list
    manage.py peer_invite_codes disable --label "group A"

A code's plaintext is printed once, by `create`, and never stored.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from peer_mock import invites
from peer_mock.models import InviteCode


class Command(BaseCommand):
    help = 'Create, list or disable peer mock invite codes.'

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest='action', required=True)
        create = sub.add_parser('create')
        create.add_argument('--label', required=True)
        create.add_argument('--max-uses', type=int, required=True)
        create.add_argument('--expires-days', type=int)
        create.add_argument('--count', type=int, default=1)
        sub.add_parser('list')
        disable = sub.add_parser('disable')
        disable.add_argument('--label', required=True)

    def handle(self, *args, action, **options):
        getattr(self, f'do_{action}')(**options)

    def do_create(self, label, max_uses, expires_days, count, **_):
        if max_uses < 1 or count < 1:
            raise CommandError('--max-uses and --count must be at least 1')
        expires_at = timezone.now() + timedelta(days=expires_days) if expires_days else None
        for _ in range(count):
            invite, code = invites.create(label, max_uses, expires_at)
            self.stdout.write(f'{code}\t{invite.label}\tmax_uses={invite.max_uses}\texpires_at={invite.expires_at}')
        self.stderr.write('Codes are shown only once; store them now.')

    def do_list(self, **_):
        for invite in InviteCode.objects.order_by('created_at'):
            self.stdout.write(f'{invite.pk}\t{invite.label}\t{invite.uses}/{invite.max_uses}\t'
                              f'active={invite.active}\texpires_at={invite.expires_at}')

    def do_disable(self, label, **_):
        updated = InviteCode.objects.filter(label=label, active=True).update(active=False)
        if not updated:
            raise CommandError(f'no active codes with label {label!r}')
        self.stdout.write(f'disabled {updated} code(s)')
