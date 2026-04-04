# Adoption Checklists

This document gives teams a practical way to adopt the starter without feeling like they must understand the entire repository on day one.

Choose the checklist that matches the level of platform capability your service needs right now.

## Feature Decision Matrix

Use this table when a team is unsure whether a capability should be enabled yet.

| Feature | Enable When | Usually Skip When | Layer |
| --- | --- | --- | --- |
| `cache` | list/read endpoints are hit frequently and DB reads are becoming a noticeable cost | traffic is still low or data changes so often that invalidation would be fragile | `Extensions` |
| `metrics` | the service is shared, business-critical, or needs alerting and dashboards | the service is still a short-lived experiment with no monitoring expectations yet | `Extensions` |
| `rate limiting` | auth endpoints are exposed beyond a tiny trusted audience, or brute-force protection matters | the service is private, temporary, and only reachable by tightly controlled internal callers | `Extensions` |
| `email/webhook providers` | the product must call external systems or notify users | those integrations do not exist yet and dry-run logs are enough for now | `Extensions` |
| `worker` | requests should stop waiting on slow side effects or long-running tasks | all work is fast, synchronous, and directly tied to the request result | `Advanced` |
| `outbox` | DB writes and async publishing must stay consistent even when the broker is unstable | the service does not publish async events yet or can tolerate occasional manual resend logic | `Advanced` |
| `ops API` | operators need safe visibility into outbox state, replay tools, or maintenance actions | there is no async platform surface to inspect or replay yet | `Advanced` |

Quick rule of thumb:

- if the feature solves a real current pain, enable it
- if the team cannot explain why it is enabled, leave it off for now
- if enabling it adds new infrastructure, confirm that the team is ready to operate that infrastructure

## Starter Profiles

If a team wants a faster default than building feature-by-feature from the matrix, start from one of these profiles.

### CRUD API Profile

Use this for:

- internal CRUD services
- admin backends
- APIs where most work is request/response over Postgres

Start with:

- `Core` only

Usually enable:

- auth
- health/readiness
- structured logging
- migrations

Usually defer:

- cache
- email/webhook providers
- worker
- outbox
- ops API

Good default mindset:

- keep the service simple until real performance or integration pressure appears

### Integration API Profile

Use this for:

- APIs that call external systems
- services that send emails or webhooks
- services that need monitoring sooner because failures often happen outside the DB

Start with:

- `Core`
- selected `Extensions`

Usually enable:

- metrics
- alerting-ready logging
- rate limiting
- provider adapters
- retry/timeout policies

Usually defer:

- worker
- outbox
- ops API

Enable Advanced later when:

- request latency becomes dominated by side effects
- external calls should no longer run inline with the request

### Async Platform Profile

Use this for:

- services that publish domain events
- systems with slow side effects or heavy async work
- services that need replay, DLQ, or background processing from early on

Start with:

- `Core`
- key `Extensions`
- selected `Advanced` features

Usually enable:

- metrics
- monitoring stack
- worker
- retry and DLQ
- outbox
- queue-depth alerting
- protected ops API

Usually defer:

- nothing critical in `Advanced`, but keep provider integrations limited to what the product really uses

Good default mindset:

- treat async processing as part of the product architecture, not just a utility bolted on later

## Core Only

Use this path if your service is a normal internal API with synchronous request handling and a database.

The service should have these decisions made:

- product name and environment values are set in `.env`
- JWT secret, issuer, and audience are replaced
- database URL points to the real environment database
- CORS origins are explicitly set for real clients
- the sample `items` module is either intentionally kept or disabled

The team should understand these parts of the repo:

- [README.md](/Users/pluto/Documents/git/fastapi101/README.md)
- [docs/architecture.md](/Users/pluto/Documents/git/fastapi101/docs/architecture.md)
- [docs/api-guide.md](/Users/pluto/Documents/git/fastapi101/docs/api-guide.md)
- [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md)
- [docs/development.md](/Users/pluto/Documents/git/fastapi101/docs/development.md)

The implementation baseline should be true:

- the first real feature follows `route -> service -> repository -> model -> schema`
- Alembic is used for schema changes
- health endpoints work in local and deploy environments
- lint, mypy, and pytest pass before merge
- Docker dev flow and production-like flow both start successfully

Core adoption is complete when:

- the team can add a new API slice without touching unrelated layers
- the service can start, migrate, authenticate, and pass tests
- the team is not blocked by worker, monitoring, or ops features they do not need yet

## Core Plus Extensions

Use this path when the service needs stronger runtime capabilities but not async platform workflows yet.

Typical reasons to adopt Extensions:

- read-heavy endpoints need caching
- the service needs Prometheus metrics and alerting hooks
- the team wants richer auth hardening and production rate limiting
- the service needs outbound email or webhook delivery
- the team wants deeper deployment and monitoring guidance

Decisions to make before enabling Extensions:

- whether cache should use `memory` or `redis`
- whether auth rate limiting should use Redis in the target environment
- whether telemetry is enabled and where it exports
- whether email/webhook delivery is dry-run, disabled, or real
- which provider adapters are actually needed

The team should read these docs in addition to Core:

- [docs/security.md](/Users/pluto/Documents/git/fastapi101/docs/security.md)
- [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)
- relevant sections in [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md)

The implementation baseline should be true:

- cache settings are explicit and invalidation behavior is understood
- metrics are exposed and scrapeable in the target environment
- alert thresholds are reviewed instead of used blindly
- provider credentials and timeouts/retry policies are explicitly set
- rate limiting behavior is tested behind the real proxy or ingress shape

Core plus Extensions adoption is complete when:

- the team can explain which Extensions are enabled and why
- monitoring and logging tell the team enough to debug normal incidents
- outbound integrations have explicit timeout/retry behavior
- no extension is enabled “just because it exists”

## Core Plus Extensions Plus Advanced

Use this path when the service needs async workflows, non-blocking integration fanout, or operational replay/repair tools.

Typical reasons to adopt Advanced:

- request handlers should not wait for emails or webhooks
- async jobs need retries and dead-letter handling
- durable background processing is part of the product
- broker publishing must be consistent with DB commits
- operators need visibility into outbox or replay workflows

Decisions to make before enabling Advanced:

- which workloads should go through the worker instead of inline request handling
- whether outbox is required for those workloads
- what retry and dead-letter policies make sense per task
- how worker idempotency is stored in multi-instance deployment
- who is allowed to use operations endpoints and replay tools

The team should read these docs in addition to Core and Extensions:

- [docs/operations.md](/Users/pluto/Documents/git/fastapi101/docs/operations.md)
- worker/outbox sections in [docs/architecture.md](/Users/pluto/Documents/git/fastapi101/docs/architecture.md)
- deployment notes for worker and dispatcher in [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)

The implementation baseline should be true:

- broker, worker, and outbox dispatcher run as separate processes
- retry, DLQ, and idempotency settings are explicit
- operations endpoints are protected and reviewed
- replay procedures are documented and tested in non-production first
- queue depth and worker failure alerts are wired into monitoring
- the team knows which tasks are safe to replay and which are not

Advanced adoption is complete when:

- async workflows can fail without silently losing business events
- operators have a safe path to inspect, replay, and recover background work
- worker scaling and API scaling can happen independently
- the team treats outbox and DLQ as operational systems, not just code paths

## Recommended Default Path

For most new internal APIs:

1. finish `Core Only`
2. add only the `Extensions` that solve a real current problem
3. adopt `Advanced` only when synchronous API flow is no longer enough

That keeps the starter powerful without making every new service carry the full platform load on day one.
