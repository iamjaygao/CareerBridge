from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import stripe
from django.conf import settings
from django.utils import timezone

from .models import Payment, PaymentSettings


@dataclass
class PayoutSettings:
    hold_days: int
    requires_admin_approval: bool
    connect_enabled: bool


def get_payout_settings() -> PayoutSettings:
    settings_obj = PaymentSettings.objects.order_by('-updated_at').first()
    if not settings_obj:
        return PayoutSettings(hold_days=2, requires_admin_approval=False, connect_enabled=True)

    return PayoutSettings(
        hold_days=int(settings_obj.payout_hold_days),
        requires_admin_approval=bool(settings_obj.payout_requires_admin_approval),
        connect_enabled=bool(settings_obj.stripe_connect_enabled),
    )


def schedule_payout_for_appointment(appointment) -> Optional[Payment]:
    payment = Payment.objects.filter(
        appointment=appointment,
        status='completed'
    ).order_by('-paid_at', '-id').first()
    if not payment:
        return None

    if payment.payout_status in ['paid', 'ready', 'pending', 'on_hold']:
        return payment

    payout_settings = get_payout_settings()
    available_at = timezone.now() + timedelta(days=payout_settings.hold_days)

    payout_status = 'pending'
    if payout_settings.hold_days == 0:
        payout_status = 'ready'

    payment.payout_status = payout_status
    payment.payout_available_at = available_at
    payment.payout_failure_reason = ''
    payment.save(update_fields=['payout_status', 'payout_available_at', 'payout_failure_reason'])
    return payment


def refresh_payout_status(payment: Payment) -> Payment:
    if payment.payout_status == 'pending' and payment.payout_available_at:
        if payment.payout_available_at <= timezone.now():
            payment.payout_status = 'ready'
            payment.save(update_fields=['payout_status'])
    return payment


def execute_payout(payment: Payment) -> Payment:
    payment = refresh_payout_status(payment)
    if payment.payout_status not in ['ready']:
        return payment

    if payment.provider != 'stripe':
        payment.payout_status = 'failed'
        payment.payout_failure_reason = 'Only Stripe payouts are supported'
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment

    if not payment.mentor or not getattr(payment.mentor, 'stripe_account_id', ''):
        payment.payout_status = 'failed'
        payment.payout_failure_reason = 'Mentor payout account not connected'
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment

    if not getattr(payment.mentor, 'payouts_enabled', False):
        payment.payout_status = 'failed'
        payment.payout_failure_reason = 'Mentor payouts not enabled'
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment

    payout_settings = get_payout_settings()
    if not payout_settings.connect_enabled:
        payment.payout_status = 'failed'
        payment.payout_failure_reason = 'Stripe Connect payouts disabled'
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment

    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if not stripe.api_key:
        payment.payout_status = 'failed'
        payment.payout_failure_reason = 'Stripe not configured'
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment

    try:
        transfer = stripe.Transfer.create(
            amount=int(payment.mentor_earnings * 100),
            currency=payment.currency.lower(),
            destination=payment.mentor.stripe_account_id,
            metadata={
                'payment_id': str(payment.id),
                'appointment_id': str(payment.appointment_id or ''),
            },
            idempotency_key=f"po_{payment.id}"
        )
        payment.payout_status = 'paid'
        payment.payout_paid_at = timezone.now()
        payment.payout_transfer_id = transfer.get('id', '')
        payment.payout_failure_reason = ''
        payment.save(update_fields=[
            'payout_status',
            'payout_paid_at',
            'payout_transfer_id',
            'payout_failure_reason',
        ])
        return payment
    except Exception as exc:
        payment.payout_status = 'failed'
        payment.payout_failure_reason = str(exc)
        payment.save(update_fields=['payout_status', 'payout_failure_reason'])
        return payment
