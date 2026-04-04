# Error Codes

This document is the central catalog for service-level and API-level error codes used by the template.

Source of truth in code:

- [`app/services/exceptions.py`](../app/services/exceptions.py)
- [`app/api/errors.py`](../app/api/errors.py)

## How To Read This Catalog

Each error code represents a stable business or infrastructure meaning.

The API layer maps those codes to HTTP status codes and returns them inside the standardized error response shape:

```json
{
  "success": false,
  "error_code": "auth.invalid_credentials",
  "message": "Invalid username or password.",
  "path": "/api/v1/auth/login",
  "request_id": "..."
}
```

## Auth Errors

### `auth.invalid_credentials`

- HTTP status: `401`
- Meaning: username/password combination is invalid
- Typical routes: `POST /api/v1/auth/login`

### `auth.inactive_user`

- HTTP status: `403`
- Meaning: user exists but is inactive and blocked from access
- Typical routes: protected endpoints and login-related flows

### `auth.invalid_token`

- HTTP status: `401`
- Meaning: token is invalid, expired, malformed, or cannot be trusted
- Typical routes: `POST /api/v1/auth/refresh`, protected endpoints

### `auth.refresh_reused`

- HTTP status: `401`
- Meaning: refresh token was already rotated or revoked and should not be accepted again
- Typical routes: `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`

### `auth.rate_limited`

- HTTP status: `429`
- Meaning: auth endpoint rate limit has been hit
- Typical routes: login, refresh, logout

## Infrastructure Errors

### `infra.db_unavailable`

- HTTP status: `503`
- Meaning: database dependency is unavailable during readiness or dependent operations
- Typical routes: `/health/ready`

## User Errors

### `user.conflict`

- HTTP status: `400`
- Meaning: user creation/update conflicts with existing data, such as username or email already in use
- Typical routes: `POST /api/v1/users/`

### `user.not_found`

- HTTP status: `404`
- Meaning: requested user does not exist
- Typical routes: `GET /api/v1/users/{user_id}`

## Item Errors

### `item.persist_failed`

- HTTP status: `500`
- Meaning: item persistence failed unexpectedly
- Typical routes: `POST /api/v1/items/`

## Common Errors

### `common.internal_error`

- HTTP status: `500`
- Meaning: generic unexpected failure when no more specific code is available
- Typical routes: any route

## Notes For Client Developers

- use `error_code` for branching logic when needed
- use `message` for display or logs, but do not assume every message is immutable forever
- log `request_id` when investigating production issues
- handle `401`, `403`, `422`, and `429` explicitly in clients with auth flows

## Notes For Backend Developers

- prefer adding new business errors in `app/services/exceptions.py`
- keep status mapping centralized in `app/api/errors.py`
- avoid creating ad hoc string literals in routes when a reusable error code is more appropriate
