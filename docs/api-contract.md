# API Contract Rules

## API design principles
- Backend-first. The backend defines the contract; the frontend must not guess or infer missing fields.
- Stable response shapes. Additive changes are allowed; breaking changes require a coordinated update.
- Status codes are authoritative. Client behavior follows HTTP status codes, not ad-hoc message strings.
- Errors are structured. All error handling routes through the shared error contract.

## Error semantics
- 401 Authentication: The user is not authenticated or the session is invalid. Clients must prompt re-authentication.
- 403 Authorization: The user is authenticated but not permitted to access the resource. Clients must not retry.
- 404 Not Found: The requested resource does not exist or is not visible to the user.
- 429 Rate Limiting: The request exceeded configured limits. Clients should back off and inform the user.
- 5xx External/Service failures: Upstream or internal service failures. Clients should present a safe error state and avoid retry loops.

## ApiError definition
`ApiError` is the canonical frontend error shape.

```ts
export interface ApiError {
  message: string;
  code?: string;
  field?: string;
}
```

- `message` is required and user-facing after mapping.
- `code` is an optional classifier used for consistent messaging and handling.
- `field` is optional and used for field-level validation errors.

## errorHandler and ErrorAlert rules
- All errors from API calls must be passed through `handleApiError` or created via `createApiError`.
- `ErrorAlert` renders `ApiError` only and derives display text via the centralized mapping.
- `ErrorAlert` must NEVER receive raw strings.
- UI components that hold error state must store `ApiError | null`, not `string`.

## Enforcement expectations
- Frontend error handling should be deterministic and mapped to status code semantics.
- Backend responses should include enough context to populate `ApiError.message` without leaking sensitive data.
- Any new endpoint must document its error codes and follow these rules before release.
