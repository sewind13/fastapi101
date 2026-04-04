# Security Guide

This template includes a strong auth baseline, but it is still a starter. Use this guide to understand what is already provided and what to harden next.

## What The Template Includes

- password hashing
- JWT access tokens
- refresh tokens with rotation
- revoked-token tracking
- logout via refresh-token revocation
- inactive-user access blocking
- auth audit logging
- baseline auth rate limiting

Core files:

- [`app/core/security.py`](../app/core/security.py)
- [`app/api/deps.py`](../app/api/deps.py)
- [`app/api/v1/auth.py`](../app/api/v1/auth.py)
- [`app/services/auth_service.py`](../app/services/auth_service.py)
- [`app/db/models/revoked_token.py`](../app/db/models/revoked_token.py)
- [`app/db/repositories/revoked_token.py`](../app/db/repositories/revoked_token.py)

## Password Policy

New passwords are validated against policy settings in `SECURITY__*`.

The template supports:

- minimum length
- optional uppercase requirement
- optional lowercase requirement
- optional digit requirement
- optional special-character requirement
- rejecting passwords that contain the username
- rejecting passwords that contain the email local part

This keeps the default policy approachable for development while still letting production environments tighten it without changing code.

## Email Verification

The template includes a baseline email-verification flow.

Current behavior:

- new users are created with `email_verified=false` when verification is enabled
- registration queues a verification email through the outbox/worker flow
- authenticated users can request a fresh verification email
- verification links confirm the email through the API and flip `email_verified=true`

Relevant endpoints:

- `POST /api/v1/auth/verify-email/request`
- `GET /api/v1/auth/verify-email/confirm?token=...`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`

Relevant config:

- `APP__PUBLIC_BASE_URL`
- `SECURITY__EMAIL_VERIFICATION_ENABLED`
- `SECURITY__EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES`
- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN`

## Password Reset

The template also includes a baseline password-reset flow.

Current behavior:

- password-reset requests always return a generic success message so the API does not reveal whether the email exists
- if the email exists, a reset email is queued through the outbox/worker flow
- reset confirmation validates a signed token and applies the same password policy as registration
- a successful reset also clears account lockout state

## Auth Flow

Endpoints:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Lifecycle:

1. user logs in with username/password
2. credentials are validated in the auth service
3. app issues access + refresh tokens
4. access tokens authorize protected routes
5. refresh tokens rotate into a new pair
6. used or logged-out refresh tokens are recorded in `revoked_token`
7. expired revoked-token rows should be cleaned up by scheduled maintenance

## Rate Limiting

The template includes auth-focused rate limiting:

- login is limited by `IP + username`
- refresh/logout are limited by client IP
- backend can be `memory` or `redis`
- proxy-aware client IP extraction can be enabled for trusted reverse proxies

Config group:

- `AUTH_RATE_LIMIT__*`

Important caveat:

- `memory` backend is process-local and suited to development or single-instance setups
- `redis` backend shares state across instances and is the intended production baseline for this template
- only trust `X-Forwarded-For` / `X-Real-IP` when the direct peer is in `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- for very high-scale public APIs, you may still want additional rate limiting at the API gateway or edge/WAF layer

## Account Lockout

The template also persists failed login state on the user record.

Current behavior:

- failed password attempts increment `failed_login_attempts`
- once the configured threshold is reached, `locked_until` is set
- while the account is locked, login returns `423 Locked`
- a successful login clears previous failed-attempt state

Relevant config:

- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_ENABLED`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_MAX_ATTEMPTS`
- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_SECONDS`

This gives you two complementary protections:

- request-level throttling through the rate limiter
- account-level lockout that survives across app instances because it is stored in the database

## Roles And Privileged Endpoints

The template uses a simple role model on the `user` table instead of username-based admin checks.

Current built-in roles:

- `user`
- `ops_admin`
- `platform_admin`

The application exposes a convenience property `is_ops_admin` on the user model, but the persisted source of truth is `role`.

Use this pattern as a baseline:

- regular product users keep `role="user"`
- users who need access to `/api/v1/ops/*` should use `role="ops_admin"` or `role="platform_admin"`
- do not grant privileged access based on usernames or email addresses alone

If your product needs more granular permissions later, extend this into a proper RBAC model rather than adding more boolean flags.

Treat the current role model as a secure baseline for internal starters, not as a final authorization system for large products. If privileged surfaces expand beyond a few operations endpoints, plan a role-permission or policy-based authorization model.

## Registration Policy

Public registration is controlled by `API__PUBLIC_REGISTRATION_ENABLED`.

Recommended usage:

- keep it `true` for products that intentionally allow public sign-up
- set it to `false` for internal-only services, admin backends, or deployment environments where users should be provisioned through an internal flow
- in production, do not leave public registration enabled at the same time as privileged operations endpoints unless that tradeoff is intentional and reviewed

When public registration is disabled, `POST /api/v1/users/` returns `403`.

## Outbound Webhook Guardrails

Outbound webhooks can become an SSRF risk if arbitrary targets are allowed.

The template includes a baseline guard:

- `WEBHOOK__REQUIRE_HTTPS=true` enforces HTTPS targets
- `WEBHOOK__ALLOW_PRIVATE_TARGETS=false` blocks localhost, private IPs, loopback, link-local, multicast, and similar internal targets
- `WEBHOOK__ALLOWED_HOSTS` restricts generic webhook delivery to an explicit host allowlist

Recommended production setup:

- keep `WEBHOOK__ALLOW_PRIVATE_TARGETS=false`
- keep `WEBHOOK__REQUIRE_HTTPS=true`
- set `WEBHOOK__ALLOWED_HOSTS` explicitly for every outbound integration host you trust
- if you use the Slack provider, keep Slack targets on `hooks.slack.com` unless your organization intentionally fronts Slack delivery through a trusted relay

Do not treat these checks as your only defense. Pair them with egress controls, DNS policy, and network-layer restrictions when possible.

## Trusted Proxy Strategy

If your app runs behind Nginx, an ingress controller, or a cloud load balancer, the direct peer seen by the API server is often the proxy, not the real client.

The template supports proxy-aware client IP extraction for rate limiting, but only when all of these are true:

- `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=true`
- the direct peer IP is inside `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- the proxy sends `X-Forwarded-For` or `X-Real-IP`

This design is intentional. Forwarded IP headers are easy to spoof if the app accepts them from arbitrary clients.

Recommended production setup:

- keep `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=false` unless the app is definitely behind trusted reverse proxies
- set `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS` to the CIDR blocks used by your ingress or load balancer layer
- ensure the proxy overwrites forwarded IP headers instead of appending untrusted values blindly
- keep edge rate limiting in the gateway/WAF for public internet traffic and use application rate limiting as a second layer

### Nginx Example

Example reverse-proxy headers:

```nginx
location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://app:8000;
}
```

Example app config:

```env
AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS="true"
AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS='["10.0.0.0/8","192.168.0.0/16"]'
```

Use CIDRs that match the addresses your app sees as direct peers inside your network, not public client ranges.

### Kubernetes / Ingress Guidance

If you run behind an ingress controller:

- identify the source IP range that reaches the app pods
- set that range in `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
- verify with logs that the direct peer IP belongs to the ingress tier
- verify that client IP extraction still behaves correctly after ingress or load balancer changes

When in doubt, leave forwarded-header trust disabled and rely on edge rate limiting first.

## Security Hardening Still Worth Adding

Depending on product needs, consider adding:

- password strength policy
- account lock/unlock workflow persisted in the database
- email verification
- MFA or step-up auth hooks
- device/session management
- secret rotation playbook
- asymmetric JWT signing if you need multi-service verification

## Minimum Production Checklist

- replace `SECURITY__SECRET_KEY`
- set product-specific `SECURITY__ISSUER`
- set product-specific `SECURITY__AUDIENCE`
- configure `API__CORS_ORIGINS`
- review `API__PUBLIC_REGISTRATION_ENABLED`
- set `AUTH_RATE_LIMIT__BACKEND="redis"`
- configure `AUTH_RATE_LIMIT__REDIS_URL`
- review `AUTH_RATE_LIMIT__*` against your traffic pattern
- review user roles for privileged endpoints
- configure `WEBHOOK__ALLOWED_HOSTS` before enabling real webhook delivery
- ensure cleanup for `revoked_token` is scheduled
