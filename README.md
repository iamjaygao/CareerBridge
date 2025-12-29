# CareerBridge

## What is CareerBridge
CareerBridge is a full-stack career preparation system that combines resume analysis, mentor discovery and booking, and job-matching signals. It is built as a Django REST API with a React frontend, and integrates with external services for resume matching, job crawling, and payments.

## Why this project matters
The system handles sensitive user data (resumes, assessments, payments) and therefore prioritizes governance over feature breadth. The core value is consistent assessment workflows that are auditable, rate-limited, and explicit about user consent and data minimization. The codebase is designed to reduce ambiguous API behavior, prevent unsafe data exposure, and keep external service failures from corrupting the user experience.

## Architecture overview
- Frontend: React application under `frontend/`.
- Backend API: Django REST Framework under `careerbridge/`.
- Payments: Stripe PaymentIntents for booking flows.
- External services: ResumeMatcher and JobCrawler (kept as separate services in this repository).
- Data: PostgreSQL (primary storage) with service-specific caches where needed.

## Key engineering decisions
- Backend-first API contract. The frontend does not infer API behavior; it relies on explicit response shapes and status codes.
- Unified error model. Errors are normalized into a shared `ApiError` structure and rendered through a single UI component.
- Consent and safety gates for AI analysis. Requests require explicit consent, data minimization, and response whitelisting.
- Strict payment binding. Every payment is attached to a known appointment or service context; orphaned intents are not allowed.
- External services are isolated. Failures are surfaced as service-level errors rather than mixed with validation errors.

## Current system status
- Resume analysis, mentor booking, and payments are implemented and in use.
- External services (ResumeMatcher, JobCrawler) are optional and integrated via service APIs.
- The system expects environment-specific keys for OpenAI and Stripe to enable analysis and payments.

## What is intentionally not included
- Additional payment rails (PayPal, bank transfers, crypto, ACH) to reduce compliance and reconciliation risk.
- Deployment or hosting instructions. This repository focuses on code and system behavior, not platform-specific operations.
- UI polish initiatives or design refreshes that do not affect correctness, consent, or security.

## How to explore the codebase
- `careerbridge/`: Django apps, API endpoints, models, and service integrations.
- `frontend/src/`: UI, API clients, error handling, and page flows.
- `docs/`: Governance rules and system constraints for API, payment, and safety behavior.
- `docs/historical/`: Prior README content retained for reference only.
