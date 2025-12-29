# System Constraints

## Stable and frozen areas
- API status code semantics are fixed and must not be repurposed.
- `ApiError` shape and `errorHandler` mappings are stable contracts.
- Consent gating for AI analysis is mandatory for all analysis entry points.
- Payment intents must always be bound to a known appointment or service.
- External service boundaries (ResumeMatcher, JobCrawler, Stripe) are isolated and must not leak internal state.

## Rules for new features
- Follow backend-first API design; do not require frontend inference.
- All errors must map to `ApiError` and render through `ErrorAlert`.
- AI-related features must enforce data minimization and output whitelisting.
- Security-sensitive actions must be auditable and rate-limited.

## Intentionally deferred or excluded
- Additional payment methods beyond Stripe cards.
- UI redesigns or aesthetic-only changes.
- New AI capabilities without consent, retention, and audit controls.
- Feature work that bypasses API contract or error semantics.
