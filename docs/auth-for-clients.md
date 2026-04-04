# Auth For Clients

This guide explains authentication from the point of view of an API consumer.

## Endpoints

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/billing/me/entitlements`
- `GET /api/v1/billing/me/usage`
- `GET /api/v1/billing/me/usage/report`
- `GET /api/v1/billing/me/balance/{resource_key}`
- `GET /api/v1/billing/me/summary`

## What Tokens Mean

- access token: used on protected requests
- refresh token: used to rotate into a fresh token pair

The template uses bearer tokens:

```http
Authorization: Bearer <access_token>
```

## Login

Send form data:

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

Fields:

- `username`
- `password`

Success response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "access_expires_in": 1800,
  "refresh_expires_in": 604800
}
```

## Refresh

Use the current refresh token:

```json
{
  "refresh_token": "..."
}
```

Important behavior:

- refresh rotates the token pair
- the previous refresh token should be treated as invalid after use
- if a revoked/old refresh token is reused, the API returns `401`

## Logout

Logout also uses the refresh token:

```json
{
  "refresh_token": "..."
}
```

This revokes that refresh token so it cannot be used again.

## Current User

Call:

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

## Common Auth Errors

- `401 auth.invalid_credentials`: wrong username/password
- `401 auth.invalid_token`: invalid or expired token
- `401 auth.refresh_reused`: refresh token already revoked/rotated
- `403 auth.inactive_user`: user exists but is inactive
- `429 auth.rate_limited`: too many auth attempts

Example `429` response:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json
X-Request-ID: 9f6e0a9c-f5c4-4ff4-a7a8-9cc4b2f6f4f1
```

```json
{
  "success": false,
  "error_code": "auth.rate_limited",
  "message": "Too many authentication attempts. Please try again later.",
  "path": "/api/v1/auth/login",
  "request_id": "9f6e0a9c-f5c4-4ff4-a7a8-9cc4b2f6f4f1"
}
```

`Retry-After` is the number of seconds the client should wait before retrying the same auth flow.

## Client Recommendations

- store access tokens and refresh tokens separately and carefully
- rotate your stored refresh token after every successful refresh
- handle `401` by attempting refresh once, not in an infinite loop
- treat `429` as a backoff signal
- log `request_id` from error responses if you need support/debugging

## Self-Service Billing Endpoints

Authenticated users can inspect the entitlements and usage tied to their own account:

- `GET /api/v1/billing/me/entitlements`
- `GET /api/v1/billing/me/usage`
- `GET /api/v1/billing/me/usage/report`
- `GET /api/v1/billing/me/balance/{resource_key}`
- `GET /api/v1/billing/me/summary`

This is useful for quota-aware clients that want to show remaining usage before attempting a gated action such as `POST /api/v1/items/`.

`GET /api/v1/billing/me/summary` is the most convenient dashboard-style endpoint. It returns:

- current entitlements
- balances grouped by `resource_key`
- recent usage events

`GET /api/v1/billing/me/usage/report` is the aggregate view. It groups usage by:

- `resource_key`
- `feature_key`
- `status`

`GET /api/v1/billing/me/usage` also supports lightweight history filtering:

- `resource_key`
- `feature_key`
- `status`
- `created_after`
- `created_before`
- `sort` (`asc` or `desc`)
- `offset`
- `limit`

Example:

```http
GET /api/v1/billing/me/usage?feature_key=items.create&sort=desc&limit=20&offset=0
Authorization: Bearer <access_token>
```

## How Clients Should Handle `429`

Recommended behavior:

1. read the `Retry-After` response header
2. wait at least that many seconds before retrying
3. avoid immediate retry loops for login, refresh, or logout
4. show a friendly message to users instead of a generic failure

Example logic:

```text
if response.status == 429:
    retry_after = int(response.headers.get("Retry-After", "60"))
    schedule_retry_after(retry_after)
```

Client-side backoff should complement server-side rate limiting. It should not try to bypass it.
