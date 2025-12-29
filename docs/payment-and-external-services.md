# Payment and External Services

## Payment entry points are intentionally limited
- Payments are only initiated through appointment or service flows.
- The system does not allow free-form or ad-hoc payment creation.
- This limits charge disputes, ensures traceability, and keeps reconciliation deterministic.

## Orphan or unbound payment intents are forbidden
- Every PaymentIntent must reference a known appointment or service context.
- Unbound intents create ambiguous ownership and inconsistent refund logic.
- The backend rejects payment requests missing context metadata.

## Stripe failure mapping
- External payment failures are mapped to 502 or 503, not 400.
- 400 is reserved for client validation errors; Stripe failures are upstream dependency errors.
- This keeps frontend behavior consistent and avoids false attribution to user input.

## External services error handling
- External calls are treated as dependency boundaries, not part of domain validation.
- ResumeMatcher and JobCrawler failures are surfaced as service errors and do not mutate core state.
- Failure responses must include a stable error code and message suitable for `ApiError` mapping.

## Supported and intentionally excluded payment methods
Supported:
- Stripe card payments via PaymentIntents.

Intentionally not supported:
- PayPal, bank transfers, crypto, and ACH. These add settlement complexity, regulatory scope, and dispute handling overhead without improving core workflow reliability.
