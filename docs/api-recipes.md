# API Recipes

This guide gives copyable examples for common workflows when building or consuming the API.

Assume the app is running locally at:

- `http://localhost:8000`

And the versioned API prefix is:

- `/api/v1`

## 1. Register A User

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "strongpassword123"
  }'
```

Expected result:

- `201 Created`
- response body shaped like `UserPublic`

## 2. Log In

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=strongpassword123"
```

Expected result:

- `200 OK`
- access token + refresh token pair

## 3. Call A Protected Route

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- current user payload

## 4. Refresh Tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

Expected result:

- `200 OK`
- new access token + new refresh token

Old refresh tokens should not be reused.

## 5. Log Out

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

Expected result:

- `200 OK`
- message response

## 6. Create An Item

Before calling this route in a fresh environment, grant the sample entitlement `item_create` to the account you want to test with. The `items` slice is the reference implementation for quota enforcement in this template.

```bash
curl -X POST http://localhost:8000/api/v1/items/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "First item",
    "description": "Created from the API recipe"
  }'
```

Expected result:

- `201 Created`
- `ItemPublic`

If the account does not have an active `item_create` entitlement, expect:

- `403 Forbidden`
- error code `billing.no_entitlement`

## 7. List Items

```bash
curl "http://localhost:8000/api/v1/items/?limit=20&offset=0" \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- JSON array

## 8. Check Your Billing Summary

If you want one dashboard-style response for the authenticated account, call:

```bash
curl http://localhost:8000/api/v1/billing/me/summary \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- current entitlements
- balances grouped by `resource_key`
- recent usage events

This is the fastest way to confirm whether a test account can still call `POST /api/v1/items/`.

## 9. Check Remaining Balance For A Resource

```bash
curl http://localhost:8000/api/v1/billing/me/balance/item_create \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- balance payload for `item_create`

Useful before and after creating items to confirm quota consumption.

## 10. Browse Usage History

```bash
curl "http://localhost:8000/api/v1/billing/me/usage?resource_key=item_create&status=committed&sort=desc&offset=0&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- paginated usage history
- `total_count`, `has_next`, and `has_prev`

Supported filters:

- `resource_key`
- `feature_key`
- `status`
- `created_after`
- `created_before`
- `sort`
- `offset`
- `limit`

## 11. Read An Aggregate Usage Report

```bash
curl "http://localhost:8000/api/v1/billing/me/usage/report?resource_key=item_create" \
  -H "Authorization: Bearer <access_token>"
```

Expected result:

- `200 OK`
- aggregate rows grouped by `resource_key`, `feature_key`, and `status`

This is useful for account dashboards or simple reporting without downloading the full event stream.

## 12. Handle Common Errors

Typical cases:

- `401`: bad credentials, invalid token, refresh reuse
- `403`: inactive user
- `403`: no entitlement / exhausted access for a gated feature
- `422`: request body/query validation error
- `429`: auth rate limited

## Background Task Follow-Up

After successful user registration, the template queues follow-up work for:

- `user.registered`
- `email.send_welcome`
- `webhook.user_registered`

These do not block the API response. They flow through the outbox dispatcher and worker processes.

Example error body:

```json
{
  "success": false,
  "error_code": "auth.invalid_credentials",
  "message": "Invalid username or password.",
  "path": "/api/v1/auth/login",
  "request_id": "..."
}
```

## 13. Add A New Resource By Copying The Pattern

If you want to add a new module like `orders`, copy the structure of:

- [`app/schemas/item.py`](../app/schemas/item.py)
- [`app/db/models/item.py`](../app/db/models/item.py)
- [`app/db/repositories/item.py`](../app/db/repositories/item.py)
- [`app/services/item_service.py`](../app/services/item_service.py)
- [`app/api/v1/items.py`](../app/api/v1/items.py)

Then register it in:

- [`app/api/v1/router.py`](../app/api/v1/router.py)

And add tests.
