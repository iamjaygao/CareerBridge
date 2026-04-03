# CareerBridge Payment Integration Guide

## Payment System Overview

CareerBridge uses Stripe PaymentIntents for mentor session payments and other paid workflows.
Additional payment providers are intentionally not supported to keep compliance and reconciliation
deterministic.

## Supported Provider

- Stripe (cards via PaymentIntents)

## Payment Flow
1. User initiates payment (booking appointment or service flow).
2. Backend creates a PaymentIntent bound to a known appointment or service.
3. Frontend confirms payment with Stripe.
4. Stripe notifies backend via webhook.
5. Backend updates payment status and triggers business logic.

## Environment Configuration
```env
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Notes
- Orphaned or unbound payment intents are rejected.
- Stripe failures are mapped to 5xx to reflect upstream dependency errors.
