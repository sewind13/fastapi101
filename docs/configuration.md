# Configuration Reference

This document explains what each configuration group does and how the main variables affect the application.

The source of truth for settings is [app/core/config.py](/Users/pluto/Documents/git/fastapi101/app/core/config.py). Full example values live in [/.env.example](/Users/pluto/Documents/git/fastapi101/.env.example), and a smaller baseline lives in [/.env.min.example](/Users/pluto/Documents/git/fastapi101/.env.min.example).

## How Configuration Is Loaded

The application uses `pydantic-settings` with nested environment variables.

Example:

```env
APP__NAME="FastAPI Template"
DATABASE__URL="postgresql+psycopg://app:app@db:5432/app"
SECURITY__ISSUER="your-template"
```

Nested groups map to settings objects:

- `APP__*` -> `AppSettings`
- `EXAMPLES__*` -> `ExampleSettings`
- `API__*` -> `APISettings`
- `SECURITY__*` -> `SecuritySettings`
- `AUTH_RATE_LIMIT__*` -> `AuthRateLimitSettings`
- `DATABASE__*` -> `DatabaseSettings`
- `LOGGING__*` -> `LoggingSettings`
- `TELEMETRY__*` -> `TelemetrySettings`
- `METRICS__*` -> `MetricsSettings`
- `EXTERNAL__*` -> `ExternalSettings`
- `EXTERNAL_EVENT_POLICIES__*` -> `ExternalEventPoliciesSettings`
- `CACHE__*` -> `CacheSettings`
- `OPS__*` -> `OpsSettings`
- `EMAIL__*` -> `EmailSettings`
- `WEBHOOK__*` -> `WebhookSettings`
- `WORKER__*` -> `WorkerSettings`
- `HEALTH__*` -> `HealthSettings`

The settings layer also supports some older flat env names for compatibility, but new projects should prefer the nested format.

## Quick Reference Table

| Variable | Default | Required To Change | Purpose |
| --- | --- | --- | --- |
| `APP__NAME` | `FastAPI Template` | Yes | App title and docs label |
| `APP__ENV` | `development` | Usually | Logical environment name |
| `APP__PUBLIC_BASE_URL` | `http://localhost:8000` | Yes when verification links are sent | Public base URL used to build verification links |
| `EXAMPLES__ENABLE_ITEMS_MODULE` | `true` | Optional | Keeps or disables the sample `items` module |
| `API__V1_PREFIX` | `/api/v1` | Optional | Base API version prefix |
| `SECURITY__SECRET_KEY` | sample value | Yes | JWT signing secret |
| `SECURITY__ISSUER` | `fastapi-template` | Yes | JWT issuer claim |
| `SECURITY__AUDIENCE` | `fastapi-template-users` | Yes | JWT audience claim |
| `SECURITY__PASSWORD_MIN_LENGTH` | `8` | Optional | Minimum password length |
| `SECURITY__EMAIL_VERIFICATION_ENABLED` | `true` | Optional | Enables email verification for new users |
| `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN` | `false` | Optional | Blocks login until `email_verified=true` |
| `AUTH_RATE_LIMIT__BACKEND` | `memory` | Yes in production | Rate-limit backend, `memory` or `redis` |
| `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS` | `false` | Optional | Trust proxy headers such as `X-Forwarded-For` for client IP extraction |
| `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_ENABLED` | `true` | Optional | Enables persisted account lockout after repeated failed passwords |
| `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_MAX_ATTEMPTS` | `5` | Optional | Failed-password threshold before the account is locked |
| `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_SECONDS` | `900` | Optional | Lockout duration in seconds once the threshold is reached |
| `AUTH_RATE_LIMIT__LOGIN_MAX_ATTEMPTS` | `5` | Optional | Failed login attempts allowed per IP+username window |
| `AUTH_RATE_LIMIT__TOKEN_MAX_ATTEMPTS` | `20` | Optional | Refresh/logout requests allowed per IP window |
| `DATABASE__URL` | `sqlite:///./database.db` | Yes | Main database connection string |
| `LOGGING__LEVEL` | `INFO` | Optional | Main application log level |
| `LOGGING__ACCESS_LOG_SAMPLE_RATE` | `1.0` | Optional | Access-log sampling rate |
| `TELEMETRY__ENABLED` | `false` | Optional | Enables OpenTelemetry |
| `TELEMETRY__SERVICE_NAME` | `fastapi-template` | Yes in production | Service name sent to telemetry backend |
| `METRICS__ENABLED` | `true` | Optional | Enables Prometheus metrics endpoint |
| `METRICS__PATH` | `/metrics` | Optional | Path used for Prometheus scraping |
| `METRICS__AUTH_TOKEN` | empty | Yes in production when metrics enabled | Bearer token required by the `/metrics` endpoint when configured |
| `EXTERNAL__MAX_ATTEMPTS` | `3` | Optional | Maximum retry attempts for external dependency calls |
| `EXTERNAL__TIMEOUT_SECONDS` | `10.0` | Optional | Shared timeout baseline for external dependency calls |
| `SMTP__MAX_ATTEMPTS` | `3` | Optional | SMTP-specific retry attempts override |
| `SENDGRID__MAX_ATTEMPTS` | `3` | Optional | SendGrid-specific retry attempts override |
| `SES__MAX_ATTEMPTS` | `3` | Optional | SES-specific retry attempts override |
| `WEBHOOK__MAX_ATTEMPTS` | `3` | Optional | Webhook-specific retry attempts override |
| `EXTERNAL_EVENT_POLICIES__EMAIL_SEND_PASSWORD_RESET__MAX_ATTEMPTS` | unset | Optional | Event-specific retry attempts for password-reset emails |
| `EXTERNAL_EVENT_POLICIES__WEBHOOK_WORKER_FAILURE_ALERT__MAX_ATTEMPTS` | unset | Optional | Event-specific retry attempts for worker-failure alerts |
| `CACHE__ENABLED` | `false` | Optional | Enables application-level read cache |
| `CACHE__BACKEND` | `memory` | Yes in production when enabled | Cache backend, `memory` or `redis` |
| `OPS__ENABLED` | `true` | Optional | Enables protected operations endpoints |
| `EMAIL__ENABLED` | `false` | Optional | Enables real email delivery in worker tasks |
| `EMAIL__DRY_RUN` | `true` | Optional | Logs email tasks without sending them |
| `EMAIL__PROVIDER` | `smtp` | Optional | Selects `smtp`, `sendgrid`, or `ses` delivery adapter |
| `WEBHOOK__ENABLED` | `false` | Optional | Enables real webhook delivery in worker tasks |
| `WEBHOOK__DRY_RUN` | `true` | Optional | Logs webhook tasks without sending them |
| `WEBHOOK__PROVIDER` | `generic` | Optional | Selects `generic` or `slack` outbound webhook adapter |
| `WORKER__ENABLED` | `false` | Optional | Enables the AMQP background worker integration |
| `WORKER__BROKER_URL` | empty | Yes when worker enabled | AMQP broker URL used by publishers and workers |
| `WORKER__QUEUE_NAME` | `app.default` | Optional | Queue name used for durable background tasks |
| `WORKER__RETRY_QUEUE_NAME` | `app.default.retry` | Optional | Retry queue used for delayed worker retries |
| `WORKER__DEAD_LETTER_QUEUE_NAME` | `app.default.dlq` | Optional | Dead-letter queue used after retries are exhausted |
| `WORKER__MAX_RETRY_DELAY_MS` | `300000` | Optional | Maximum backoff delay for retried tasks |
| `WORKER__IDEMPOTENCY_ENABLED` | `true` | Optional | Enables duplicate protection for worker task processing |
| `WORKER__IDEMPOTENCY_BACKEND` | `memory` | Optional | Backend used for worker idempotency state |
| `WORKER__IDEMPOTENCY_REDIS_URL` | empty | Yes when Redis idempotency used | Redis URL for distributed idempotency state |
| `HEALTH__ENABLE_REDIS_CHECK` | `false` | Optional | Enables Redis `PING` readiness check |
| `HEALTH__ENABLE_S3_CHECK` | `false` | Optional | Enables S3 `head_bucket` readiness check |
| `HEALTH__ENABLE_QUEUE_CHECK` | `false` | Optional | Enables AMQP connection readiness check |

Use this table for quick scanning. The sections below explain each group in more detail.

## `APP__*`

Application metadata and environment mode.

- `APP__NAME`
  Used as the FastAPI app title and appears in generated API docs.

- `APP__DEBUG`
  General-purpose debug flag for the application. This template does not wire every behavior to it automatically, but it is useful for your own environment-specific logic.

- `APP__ENV`
  Logical environment name such as `development`, `staging`, or `production`.

- `APP__PUBLIC_BASE_URL`
  Public base URL used to build email-verification links such as `http://localhost:8000` or `https://api.example.com`.

## `EXAMPLES__*`

Controls optional example modules that ship with the template.

- `EXAMPLES__ENABLE_ITEMS_MODULE`
  Enables or disables the example `items` feature slice. Set it to `false` when starting a product that does not want the sample module exposed.

## `API__*`

API routing and CORS behavior.

- `API__V1_PREFIX`
  Base prefix for versioned routes. Default is `/api/v1`.

- `API__CORS_ORIGINS`
  List of allowed origins for browser-based cross-origin requests. Can be a JSON array or a comma-separated string.

## `SECURITY__*`

JWT and authentication behavior.

- `SECURITY__SECRET_KEY`
  Secret used to sign JWTs. This must be replaced with a strong real value before production use.

- `SECURITY__ALGORITHM`
  JWT signing algorithm. Default is `HS256`.

- `SECURITY__ISSUER`
  JWT `iss` claim. Use a stable product-specific identifier.

- `SECURITY__AUDIENCE`
  JWT `aud` claim. Use a stable audience string expected by your application.

- `SECURITY__ACCESS_TOKEN_EXPIRE_MINUTES`
  Access token lifetime in minutes.

- `SECURITY__REFRESH_TOKEN_EXPIRE_MINUTES`
  Refresh token lifetime in minutes.

- `SECURITY__PASSWORD_MIN_LENGTH`
  Minimum password length enforced by the password-policy validator.

- `SECURITY__PASSWORD_REQUIRE_UPPERCASE`
  Requires at least one uppercase letter in new passwords.

- `SECURITY__PASSWORD_REQUIRE_LOWERCASE`
  Requires at least one lowercase letter in new passwords.

- `SECURITY__PASSWORD_REQUIRE_DIGIT`
  Requires at least one digit in new passwords.

- `SECURITY__PASSWORD_REQUIRE_SPECIAL`
  Requires at least one non-alphanumeric character in new passwords.

- `SECURITY__PASSWORD_FORBID_USERNAME`
  Rejects passwords that contain the username.

- `SECURITY__PASSWORD_FORBID_EMAIL_LOCALPART`
  Rejects passwords that contain the email local part before the `@`.

- `SECURITY__EMAIL_VERIFICATION_ENABLED`
  Enables email-verification support and marks new users as unverified until they confirm.

- `SECURITY__EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES`
  Expiration window for email-verification tokens.

- `SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN`
  When `true`, login is blocked until the user verifies their email address.

## `AUTH_RATE_LIMIT__*`

Authentication endpoint throttling.

- `AUTH_RATE_LIMIT__ENABLED`
  Enables baseline in-process rate limiting for auth endpoints.

- `AUTH_RATE_LIMIT__BACKEND`
  Backend used for rate limiting. Use `redis` for real multi-instance production.

- `AUTH_RATE_LIMIT__REDIS_URL`
  Redis connection URL used when the rate-limit backend is `redis`.

  For local development, the optional compose Redis profile uses `redis://redis:6379/0` from inside the app containers. For production-like environments, prefer an external or managed Redis URL.

- `AUTH_RATE_LIMIT__KEY_PREFIX`
  Prefix used for rate-limit keys stored in the backend.

- `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS`
  Enables trusted proxy header parsing for client IP extraction. Only enable this when your app is behind known trusted proxies.

- `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS`
  List of trusted proxy CIDRs allowed to supply forwarded client IP headers. If the direct client IP is not in this list, forwarded headers are ignored.

- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_ENABLED`
  Enables persisted account lockout state on the user record. This is separate from request throttling and survives across app instances.

- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_MAX_ATTEMPTS`
  Number of failed password attempts allowed before the account is temporarily locked.

- `AUTH_RATE_LIMIT__ACCOUNT_LOCKOUT_SECONDS`
  Lockout duration in seconds once the failed-attempt threshold is reached.

- `AUTH_RATE_LIMIT__LOGIN_MAX_ATTEMPTS`
  Number of failed login attempts allowed within the login window for the same `IP + username` pair.

- `AUTH_RATE_LIMIT__LOGIN_WINDOW_SECONDS`
  Time window used to count failed login attempts.

- `AUTH_RATE_LIMIT__TOKEN_MAX_ATTEMPTS`
  Number of refresh/logout requests allowed within the token window for the same client IP.

- `AUTH_RATE_LIMIT__TOKEN_WINDOW_SECONDS`
  Time window used to count refresh/logout requests.

## `DATABASE__*`

Database connection and connection-pool settings.

- `DATABASE__URL`
  Main SQLAlchemy/SQLModel connection string. This is the single most important DB setting.

- `DATABASE__ECHO`
  Enables SQLAlchemy SQL logging when set to `true`.

- `DATABASE__POOL_SIZE`
  Base number of persistent DB connections kept in the pool for non-SQLite databases.

- `DATABASE__MAX_OVERFLOW`
  Number of extra temporary connections that can be created above `POOL_SIZE`.

- `DATABASE__POOL_TIMEOUT`
  How long to wait for a pooled connection before failing.

- `DATABASE__POOL_RECYCLE`
  Number of seconds before a connection is recycled to avoid stale connections.

## `LOGGING__*`

Structured logging behavior.

- `LOGGING__LEVEL`
  Log level for the main application logger.

- `LOGGING__AUDIT_LEVEL`
  Log level for the audit logger used for auth/security-significant events.

- `LOGGING__SCHEMA_VERSION`
  Stable schema version string included in logs so downstream consumers can evolve parsers safely.

- `LOGGING__ACCESS_LOG_SAMPLE_RATE`
  Sampling rate for successful access logs. Use a value between `0.0` and `1.0`.

- `LOGGING__ACCESS_LOG_SKIP_PATHS`
  Exact path list to suppress from access logs unless they error.

- `LOGGING__ACCESS_LOG_SKIP_PREFIXES`
  Prefix-based path suppression for noisy route groups.

- `LOGGING__TRACE_HEADER_NAME`
  Header name used to read incoming trace context when OpenTelemetry is not directly providing one.

## `TELEMETRY__*`

OpenTelemetry integration.

- `TELEMETRY__ENABLED`
  Enables or disables OpenTelemetry setup.

- `TELEMETRY__SERVICE_NAME`
  Service name reported to the telemetry backend.

- `TELEMETRY__SERVICE_VERSION`
  Service version reported to the telemetry backend.

- `TELEMETRY__EXPORTER_OTLP_ENDPOINT`
  OTLP endpoint to send traces to.

- `TELEMETRY__EXPORTER_OTLP_INSECURE`
  Controls whether the OTLP exporter uses insecure transport.

## `HEALTH__*`

Health and readiness behavior.

- `HEALTH__TIMEOUT_SECONDS`
  Timeout used by optional client-based readiness checks.

- `HEALTH__ENABLE_REDIS_CHECK`
  Enables the Redis readiness check.

- `HEALTH__REDIS_URL`
  Connection URL used for the Redis readiness check. The app uses a real Redis client and sends `PING`.

  Typical local setup:
  reuse the same Redis instance as auth rate limiting, often on `/0`.

- `HEALTH__ENABLE_S3_CHECK`
  Enables the S3 readiness check.

- `HEALTH__S3_ENDPOINT_URL`
  Endpoint used for the S3 readiness check.

- `HEALTH__S3_BUCKET_NAME`
  Bucket name used for the S3 readiness check. The app uses a real S3 client and calls `head_bucket`, so this must point to a bucket the app can access.

- `HEALTH__S3_REGION`
  Optional region for the S3 readiness check.

- `HEALTH__ENABLE_QUEUE_CHECK`
  Enables the queue/broker readiness check.

- `HEALTH__QUEUE_URL`
  Connection URL used for the queue readiness check. The app uses a real AMQP client and opens a broker connection.

## `METRICS__*`

Prometheus metrics exposure.

- `METRICS__ENABLED`
  Enables the Prometheus metrics endpoint.

- `METRICS__PATH`
  Path that serves Prometheus-formatted metrics.

- `METRICS__INCLUDE_IN_SCHEMA`
  Controls whether the metrics endpoint appears in generated OpenAPI docs.

- `METRICS__AUTH_TOKEN`
  Optional bearer token for the metrics endpoint. When set, callers must send `Authorization: Bearer <token>`. In production, this template expects a metrics auth token whenever metrics are enabled.

## `EXTERNAL__*`

Shared timeout and retry policy for outbound dependency calls.

- `EXTERNAL__TIMEOUT_SECONDS`
  Baseline timeout used by retry-enabled external calls such as SMTP delivery.

- `EXTERNAL__MAX_ATTEMPTS`
  Maximum number of attempts for retry-enabled external dependency calls.

- `EXTERNAL__BACKOFF_SECONDS`
  Base backoff delay before retrying an external call.

- `EXTERNAL__MAX_BACKOFF_SECONDS`
  Upper bound for retry backoff growth.

- `EXTERNAL__RETRY_ON_STATUSES`
  HTTP status codes that should be retried for urllib-based outbound calls.

Provider-specific overrides:

- `SMTP__*`
  Override timeout/retry policy for SMTP delivery without changing other external calls.

- `SENDGRID__*`
  Override timeout/retry policy for SendGrid HTTP calls.

- `SES__*`
  Override timeout/retry policy for SES API calls.

- `WEBHOOK__*`
  Override timeout/retry policy for generic and Slack webhook delivery. `WEBHOOK__TIMEOUT_SECONDS_POLICY` affects the retry policy baseline, while `WEBHOOK__TIMEOUT_SECONDS` remains the raw request timeout already used by the provider.

Event-specific overrides:

- `EXTERNAL_EVENT_POLICIES__*`
  Override retry behavior for built-in events without changing the provider-wide defaults.

Fallback order:

- event-specific policy in `EXTERNAL_EVENT_POLICIES__*`
- provider-specific policy in `SMTP__*`, `SENDGRID__*`, `SES__*`, or `WEBHOOK__*`
- shared baseline in `EXTERNAL__*`

Built-in event policy keys:

- `EXTERNAL_EVENT_POLICIES__EMAIL_SEND_WELCOME__*`
- `EXTERNAL_EVENT_POLICIES__EMAIL_SEND_PASSWORD_RESET__*`
- `EXTERNAL_EVENT_POLICIES__EMAIL_SEND_VERIFICATION__*`
- `EXTERNAL_EVENT_POLICIES__WEBHOOK_USER_REGISTERED__*`
- `EXTERNAL_EVENT_POLICIES__WEBHOOK_WORKER_FAILURE_ALERT__*`

Each event accepts the same fields:

- `TIMEOUT_SECONDS`
- `MAX_ATTEMPTS`
- `BACKOFF_SECONDS`
- `MAX_BACKOFF_SECONDS`
- `RETRY_ON_STATUSES`

## `OPS__*`

Operations endpoint configuration.

- `OPS__ENABLED`
  Enables or disables operations endpoints such as outbox status and DLQ replay.

## `CACHE__*`

Application-level read cache configuration.

- `CACHE__ENABLED`
  Enables cache lookups and writes in application services.

- `CACHE__BACKEND`
  Backend used for cache state. Use `redis` for real multi-instance production.

- `CACHE__REDIS_URL`
  Redis connection URL used when the cache backend is `redis`.

  The optional compose Redis profile in this repository uses `redis://redis:6379/2` from inside the app containers. If Redis runs outside compose, point this at the external hostname instead.

  Typical local setup:
  keep cache entries on a separate logical database such as `/2`.

- `CACHE__KEY_PREFIX`
  Prefix used for cache keys stored in the backend.

- `CACHE__DEFAULT_TTL_SECONDS`
  Default TTL used by generic cache writes.

- `CACHE__ITEMS_LIST_TTL_SECONDS`
  TTL used by the example items list cache.

### Common Redis Config Profiles

You do not need every Redis-backed feature turned on at once.

#### No Redis

```env
CACHE__ENABLED="false"
CACHE__BACKEND="memory"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="memory"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="memory"

HEALTH__ENABLE_REDIS_CHECK="false"
```

#### Cache Only

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="memory"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="memory"

HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
```

#### Full Redis Setup

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="redis"
AUTH_RATE_LIMIT__REDIS_URL="redis://redis:6379/0"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="redis"
WORKER__IDEMPOTENCY_REDIS_URL="redis://redis:6379/1"

HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
```

## `EMAIL__*`

Email-delivery configuration for worker tasks.

- `EMAIL__ENABLED`
  Enables real email delivery through the selected provider.

- `EMAIL__DRY_RUN`
  Logs email sends without making provider API calls.

- `EMAIL__PROVIDER`
  Selects the delivery adapter. Supported values are `smtp`, `sendgrid`, and `ses`.

- `EMAIL__HOST`
  SMTP host used for outgoing email when `EMAIL__PROVIDER=smtp`.

- `EMAIL__PORT`
  SMTP port used for outgoing email when `EMAIL__PROVIDER=smtp`.

- `EMAIL__USERNAME`
  Optional SMTP username when `EMAIL__PROVIDER=smtp`.

- `EMAIL__PASSWORD`
  Optional SMTP password when `EMAIL__PROVIDER=smtp`.

- `EMAIL__USE_TLS`
  Enables `STARTTLS` before authentication and delivery when `EMAIL__PROVIDER=smtp`.

- `EMAIL__FROM_EMAIL`
  Sender address used for outgoing email across all email adapters.

- `EMAIL__SENDGRID_API_KEY`
  API key used when `EMAIL__PROVIDER=sendgrid`.

- `EMAIL__SENDGRID_API_BASE_URL`
  Override URL for SendGrid-compatible mail APIs when `EMAIL__PROVIDER=sendgrid`.

- `EMAIL__SENDGRID_TIMEOUT_SECONDS`
  Request timeout used by the SendGrid adapter.

- `EMAIL__SENDGRID_CATEGORIES`
  Optional list of SendGrid categories attached to outbound messages.

- `EMAIL__SENDGRID_CUSTOM_ARGS`
  Optional JSON object of SendGrid `custom_args` attached to the message personalization.

- `EMAIL__SENDGRID_WELCOME_TEMPLATE_ID`
  Optional SendGrid dynamic template ID used by the welcome email task. When set, the provider sends `dynamic_template_data` instead of a plain text body.

- `EMAIL__SENDGRID_PASSWORD_RESET_TEMPLATE_ID`
  Optional SendGrid dynamic template ID used by the password-reset email task.

- `EMAIL__SENDGRID_VERIFICATION_TEMPLATE_ID`
  Optional SendGrid dynamic template ID used by the email-verification task.

- `EMAIL__SES_REGION`
  AWS region used when `EMAIL__PROVIDER=ses`.

- `EMAIL__SES_CONFIGURATION_SET`
  Optional SES configuration set name for tagging or event publishing.

- `EMAIL__SES_PROFILE_NAME`
  Optional AWS profile name used to build a `boto3.Session` for SES delivery.

- `EMAIL__SES_ACCESS_KEY_ID`
  Optional explicit AWS access key used when not relying on instance or profile credentials.

- `EMAIL__SES_SECRET_ACCESS_KEY`
  Optional explicit AWS secret key used when not relying on instance or profile credentials.

- `EMAIL__SES_SESSION_TOKEN`
  Optional AWS session token paired with explicit SES credentials.

- `EMAIL__SES_WELCOME_TEMPLATE_NAME`
  Optional SES template name used by the welcome email task. When set, the provider calls `send_templated_email` instead of `send_email`.

- `EMAIL__SES_PASSWORD_RESET_TEMPLATE_NAME`
  Optional SES template name used by the password-reset email task.

- `EMAIL__SES_VERIFICATION_TEMPLATE_NAME`
  Optional SES template name used by the email-verification task.

## `WEBHOOK__*`

Webhook-delivery configuration for worker tasks.

- `WEBHOOK__ENABLED`
  Enables real outbound webhook delivery.

- `WEBHOOK__DRY_RUN`
  Logs webhook sends without making HTTP calls.

- `WEBHOOK__PROVIDER`
  Selects the outbound adapter. Supported values are `generic` and `slack`.

- `WEBHOOK__USER_REGISTERED_URL`
  URL used by the `webhook.user_registered` task when `WEBHOOK__PROVIDER=generic`.

- `WEBHOOK__TIMEOUT_SECONDS`
  Request timeout for outbound webhook delivery.

- `WEBHOOK__AUTH_HEADER_NAME`
  Optional header name used for webhook authentication when `WEBHOOK__PROVIDER=generic`.

- `WEBHOOK__AUTH_HEADER_VALUE`
  Optional header value used for webhook authentication when `WEBHOOK__PROVIDER=generic`.

- `WEBHOOK__SLACK_WEBHOOK_URL`
  Incoming webhook URL used when `WEBHOOK__PROVIDER=slack`.

- `WEBHOOK__SLACK_CHANNEL`
  Optional Slack channel override used when `WEBHOOK__PROVIDER=slack`.

- `WEBHOOK__SLACK_USERNAME`
  Optional Slack bot display name used when `WEBHOOK__PROVIDER=slack`.

- `WEBHOOK__SLACK_ICON_EMOJI`
  Optional Slack icon emoji used when `WEBHOOK__PROVIDER=slack`.

- `WEBHOOK__SLACK_ROUTE_URLS`
  Optional JSON object that maps logical route names to Slack incoming webhook URLs. The built-in tasks currently use `user_registered` and `worker_failure`, then fall back to `WEBHOOK__SLACK_WEBHOOK_URL`.

- `WEBHOOK__ALLOWED_HOSTS`
  Optional host allowlist for outbound webhook delivery. For the generic provider, set this before enabling real delivery in production. For the Slack provider, it can override the default `hooks.slack.com` allowlist when you intentionally route through a trusted relay.

- `WEBHOOK__ALLOW_PRIVATE_TARGETS`
  When `false`, blocks localhost, private IPs, loopback, link-local, multicast, and similar internal targets to reduce SSRF risk.

- `WEBHOOK__REQUIRE_HTTPS`
  When `true`, requires outbound webhook targets to use HTTPS.

## `API__*`

- `API__PUBLIC_REGISTRATION_ENABLED`
  Enables or disables public sign-up through `POST /api/v1/users/`. Disable this for internal-only services or environments where user creation should happen through an admin or provisioning flow.

## `WORKER__*`

Background worker configuration.

- `WORKER__ENABLED`
  Enables background task publishing and worker consumption.

- `WORKER__BROKER_URL`
  AMQP connection URL used by the worker and the task publisher.

- `WORKER__QUEUE_NAME`
  Durable queue name used for background tasks.

- `WORKER__RETRY_QUEUE_NAME`
  Queue name used for delayed retries after task failures.

- `WORKER__DEAD_LETTER_QUEUE_NAME`
  Queue name used for tasks that failed after the maximum retry count.

- `WORKER__PREFETCH_COUNT`
  AMQP prefetch count for the worker consumer. Lower values reduce per-worker concurrency pressure; higher values can improve throughput.

- `WORKER__MAX_RETRIES`
  Maximum number of retry attempts before a task is moved to the dead-letter queue.

- `WORKER__RETRY_DELAY_MS`
  Delay before a failed task returns from the retry queue back to the main worker queue.

- `WORKER__MAX_RETRY_DELAY_MS`
  Upper bound for retry backoff delay. The worker applies exponential backoff and caps it at this value.

- `WORKER__REQUEUE_ON_FAILURE`
  Controls whether failed worker deliveries are requeued instead of rejected.

- `WORKER__IDEMPOTENCY_ENABLED`
  Enables idempotency protection for worker deliveries based on task IDs.

- `WORKER__IDEMPOTENCY_BACKEND`
  Backend used for worker idempotency state. Use `redis` for multi-worker production setups.

- `WORKER__IDEMPOTENCY_REDIS_URL`
  Redis URL used when worker idempotency backend is `redis`.

  Typical local setup:
  keep worker idempotency keys on a separate logical database such as `/1`.

- `WORKER__IDEMPOTENCY_KEY_PREFIX`
  Prefix used for worker idempotency keys.

- `WORKER__IDEMPOTENCY_TTL_SECONDS`
  Retention window for worker idempotency state.

## Recommended Minimum Changes After Cloning

At a minimum, update these before serious development:

- `APP__NAME`
- `DATABASE__URL`
- `SECURITY__SECRET_KEY`
- `SECURITY__ISSUER`
- `SECURITY__AUDIENCE`
- `AUTH_RATE_LIMIT__BACKEND`
- `AUTH_RATE_LIMIT__LOGIN_MAX_ATTEMPTS`
- `TELEMETRY__SERVICE_NAME`

Also decide whether to keep or disable:

- `EXAMPLES__ENABLE_ITEMS_MODULE`

## Typical Profiles

### Local Development

Common pattern:

- `APP__ENV="development"`
- `DATABASE__URL` points to local Postgres or SQLite
- `DATABASE__ECHO="false"` or `true` if you want SQL debug output
- `TELEMETRY__ENABLED="false"`
- optional dependency checks usually disabled

### Production

Common pattern:

- `APP__ENV="production"`
- `DATABASE__URL` points to managed Postgres
- `SECURITY__SECRET_KEY` is a real secret from your secret manager
- `TELEMETRY__ENABLED="true"` when observability is configured
- readiness checks enabled only for dependencies your service truly requires to serve traffic

## Production Checklist

Before deploying to a real environment, verify these items:

1. `SECURITY__SECRET_KEY` is replaced with a strong secret from a secret manager.
2. `SECURITY__ISSUER` and `SECURITY__AUDIENCE` are product-specific and stable.
3. `AUTH_RATE_LIMIT__BACKEND="redis"` in production and `AUTH_RATE_LIMIT__REDIS_URL` is configured.
4. `AUTH_RATE_LIMIT__*` values match your expected auth traffic profile and proxy layout.
3. `DATABASE__URL` points to the real Postgres instance for that environment.
4. `APP__ENV` is set correctly, usually `production`.
5. `TELEMETRY__SERVICE_NAME` and `TELEMETRY__SERVICE_VERSION` match your deployed service.
6. `TELEMETRY__EXPORTER_OTLP_ENDPOINT` is configured if telemetry is enabled.
7. `LOGGING__LEVEL` and `LOGGING__AUDIT_LEVEL` are appropriate for production noise levels.
8. `LOGGING__ACCESS_LOG_SAMPLE_RATE` is intentionally chosen, not left accidental.
9. Only the readiness checks you truly depend on are enabled.
10. `EXAMPLES__ENABLE_ITEMS_MODULE` is disabled or removed if the sample slice should not exist in the product.

Recommended follow-up checks:

- confirm `/health/live` and `/health/ready` are wired correctly in infrastructure
- confirm migrations run before application traffic is admitted
- confirm `.env` is not used as the production secret source if your platform supports a better secret mechanism
- confirm real secrets are sourced from your secret-management system and not committed config

## Related Files

- [app/core/config.py](/Users/pluto/Documents/git/fastapi101/app/core/config.py)
- [/.env.example](/Users/pluto/Documents/git/fastapi101/.env.example)
- [app/core/logging.py](/Users/pluto/Documents/git/fastapi101/app/core/logging.py)
- [app/core/health.py](/Users/pluto/Documents/git/fastapi101/app/core/health.py)
- [app/core/telemetry.py](/Users/pluto/Documents/git/fastapi101/app/core/telemetry.py)
