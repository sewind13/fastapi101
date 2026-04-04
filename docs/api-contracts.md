# API Contracts

This document explains the API conventions that clients and backend developers should treat as stable.

## Base Prefix

The versioned API is mounted under:

- `API__V1_PREFIX`
- default: `/api/v1`

See [`app/api/router.py`](../app/api/router.py).

## Success Response Conventions

The template uses normal JSON response bodies with explicit response models.

Examples:

- user registration returns `201` with `UserPublic`
- login returns `200` with `TokenPair`
- list endpoints return `200` with an array
- logout returns `200` with `MessageResponse`

Main schema files:

- [`app/schemas/user.py`](../app/schemas/user.py)
- [`app/schemas/item.py`](../app/schemas/item.py)
- [`app/schemas/token.py`](../app/schemas/token.py)
- [`app/schemas/common.py`](../app/schemas/common.py)
- [`app/schemas/billing.py`](../app/schemas/billing.py)

## Billing Response Conventions

Self-service and ops billing endpoints use explicit wrapper models instead of raw arrays.

Common shapes include:

- entitlement lists with `entitlements`
- balance responses grouped by `resource_key`
- usage history responses with:
  - `total_count`
  - `has_next`
  - `has_prev`
  - `usage_events`
- usage report responses with `aggregates`

The usage report rows are grouped by:

- `resource_key`
- `feature_key`
- `status`

## Error Response Shape

Centralized errors use this shape:

```json
{
  "success": false,
  "error_code": "user.not_found",
  "message": "User not found.",
  "path": "/api/v1/users/999",
  "request_id": "..."
}
```

Validation errors may also include:

```json
{
  "details": [
    {
      "type": "...",
      "loc": ["body", "field_name"],
      "msg": "...",
      "input": "..."
    }
  ]
}
```

Source:

- [`app/schemas/common.py`](../app/schemas/common.py)
- [`app/main.py`](../app/main.py)

## Status Code Conventions

Common mappings in this template:

- `200`: successful read/action
- `201`: successful creation
- `400`: business conflict or bad input at service level
- `401`: invalid credentials or invalid token
- `403`: inactive/forbidden user
- `404`: resource not found
- `422`: request validation failed
- `423`: account temporarily locked
- `429`: auth rate limit hit
- `500`: internal server error
- `503`: readiness/dependency unavailable

Mapping source:

- [`app/api/errors.py`](../app/api/errors.py)

## Current Error Codes

Current service-level error codes include:

- `auth.invalid_credentials`
- `auth.inactive_user`
- `auth.invalid_token`
- `auth.refresh_reused`
- `auth.rate_limited`
- `auth.account_locked`
- `infra.db_unavailable`
- `billing.no_entitlement`
- `billing.quota_exhausted`
- `billing.entitlement_expired`
- `billing.feature_not_enabled`
- `user.conflict`
- `user.not_found`
- `item.persist_failed`
- `common.internal_error`

Source:

- [`app/services/exceptions.py`](../app/services/exceptions.py)

Full catalog:

- [error-codes.md](error-codes.md)

## Request ID

Every standardized error response includes:

- `request_id`

The app also returns `X-Request-ID` in response headers.

This is useful for:

- log correlation
- support/debug workflows
- tracing user-reported issues

## Auth Contract

Login response shape:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "access_expires_in": 1800,
  "refresh_expires_in": 604800
}
```

Protected routes expect:

```http
Authorization: Bearer <access_token>
```

Refresh/logout request body:

```json
{
  "refresh_token": "..."
}
```

See also:

- [auth-for-clients.md](auth-for-clients.md)
