# Security Hardening Checklist

Use this guide as the first hardening pass before a real shared-environment or production-like deployment.

The goal here is not to redesign the whole auth system. It is to remove unsafe defaults, review exposed surfaces, and force explicit decisions for sensitive settings.

## What To Review First

Start with these files:

- [`app/core/config.py`](../app/core/config.py)
- [`app/api/deps.py`](../app/api/deps.py)
- [`app/main.py`](../app/main.py)
- [`app/api/v1/auth.py`](../app/api/v1/auth.py)
- [`app/api/v1/ops.py`](../app/api/v1/ops.py)

## Current Template Findings To Review

These are the most important security-related defaults and behaviors visible in the current codebase.

### 1. Replace the default JWT secret before any shared deployment

The code defines a built-in fallback secret:

- [`app/core/config.py`](../app/core/config.py)

Current behavior:

- `DEFAULT_SECRET_KEY = "change-me-to-a-32-character-minimum-secret"`
- `SecuritySettings.secret_key` uses that default

Hardening action:

- set `SECURITY__SECRET_KEY` to a real high-entropy secret in every non-local environment
- the app now fails startup in non-local environments when the default secret is still present

Why it matters:

- anyone who knows the default can forge tokens if the app is deployed without overriding it

### 2. Review public registration explicitly

Current behavior:

- `API__PUBLIC_REGISTRATION_ENABLED` defaults to `true`
- `POST /api/v1/users/` respects that flag

Relevant files:

- [`app/core/config.py`](../app/core/config.py)
- [`app/api/v1/users.py`](../app/api/v1/users.py)

Hardening action:

- disable public registration for internal tools, admin backends, and staff-only services
- keep it enabled only when public self-signup is intentional

### 3. Decide whether verified email is required for login

Current behavior:

- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN` defaults to `false`

Relevant file:

- [`app/core/config.py`](../app/core/config.py)

Hardening action:

- decide explicitly whether your product should allow login before email verification
- turn it on for products where email identity matters to account safety

### 4. Do not expose `/metrics` publicly without protection

Current behavior:

- metrics are enabled by default
- `/metrics` is protected only when `METRICS__AUTH_TOKEN` is set

Relevant file:

- [`app/main.py`](../app/main.py)

Hardening action:

- keep `/metrics` internal-only through routing or network policy
- or set `METRICS__AUTH_TOKEN` and configure Prometheus to use it

Why it matters:

- metrics can leak operational topology, route names, dependency failures, and traffic shape

### 5. Treat operations endpoints as privileged surface

Current behavior:

- ops endpoints are mounted under `/api/v1/ops/*`
- access requires `get_operations_user`
- `OPS__ENABLED` defaults to `true`

Relevant files:

- [`app/api/deps.py`](../app/api/deps.py)
- [`app/api/v1/ops.py`](../app/api/v1/ops.py)
- [`app/core/config.py`](../app/core/config.py)

Hardening action:

- leave ops routes enabled only when the environment actually needs them
- review which users hold `ops_admin` or `platform_admin`
- keep ops routes off public internet routing when possible

### 6. Use Redis-backed auth rate limiting in multi-instance environments

Current behavior:

- auth rate limiting is enabled
- backend defaults to `memory`

Relevant files:

- [`app/core/config.py`](../app/core/config.py)
- [`app/api/v1/auth.py`](../app/api/v1/auth.py)
- [`docs/security.md`](./security.md)

Hardening action:

- use `AUTH_RATE_LIMIT__BACKEND="redis"` in real multi-instance environments
- configure `AUTH_RATE_LIMIT__REDIS_URL`
- only enable trusted proxy header parsing when `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS` is correct

Why it matters:

- in-memory rate limiting does not share state across replicas

### 7. Use Redis-backed worker idempotency in multi-worker environments

Current behavior:

- worker idempotency is enabled
- backend defaults to `memory`

Relevant file:

- [`app/core/config.py`](../app/core/config.py)

Hardening action:

- use `WORKER__IDEMPOTENCY_BACKEND="redis"` when more than one worker instance can process the same queue

### 8. Keep webhook delivery constrained

Current behavior:

- webhook config already has good guardrails:
  `require_https=true`, `allow_private_targets=false`

Relevant file:

- [`app/core/config.py`](../app/core/config.py)

Hardening action:

- keep those defaults
- add explicit `WEBHOOK__ALLOWED_HOSTS` for each trusted integration target

### 9. Review telemetry transport security if OTLP is enabled

Current behavior:

- telemetry exporter is disabled by default
- if enabled, `exporter_otlp_insecure` defaults to `true`

Relevant file:

- [`app/core/config.py`](../app/core/config.py)

Hardening action:

- if shipping telemetry outside a trusted local network, review TLS settings explicitly before enabling OTLP export

## Minimum Hardening Decisions Before Shared-Env Deploy

Make these decisions explicitly:

- [ ] replace `SECURITY__SECRET_KEY`
- [ ] set product-specific `SECURITY__ISSUER` and `SECURITY__AUDIENCE`
- [ ] decide whether `API__PUBLIC_REGISTRATION_ENABLED` should be `true`
- [ ] decide whether `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN` should be `true`
- [ ] restrict `API__CORS_ORIGINS` to real clients
- [ ] protect `/metrics` with internal routing or `METRICS__AUTH_TOKEN`
- [ ] review `OPS__ENABLED` and ops-admin role assignments
- [ ] move auth rate limiting to Redis for multi-instance deployment
- [ ] move worker idempotency to Redis for multi-worker deployment
- [ ] keep webhook allowlists explicit

## Recommended Next Code Hardening Tasks

After this checklist, the next code-level improvements worth making are:

1. Extend startup validation beyond the default JWT secret into other production-sensitive defaults.
2. Fail startup when multi-instance production-like settings still use in-memory rate limiting or in-memory worker idempotency.
3. Add a production config validation pass for public registration, metrics protection, and proxy trust settings.
4. Add tests that prove these startup validations fail closed.

## Related Docs

- [security.md](./security.md)
- [first-deploy-checklist.md](./first-deploy-checklist.md)
- [deployment.md](./deployment.md)
- [secret-management.md](./secret-management.md)
