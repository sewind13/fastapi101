# Platform Starter Guide

This document explains how to think about this repository as a production-ready internal platform starter instead of a minimal boilerplate.

The goal is not to make every service adopt every feature on day one. The goal is to give teams one strong shared base, with optional layers that can be turned on when the product needs them.

## Layer Model

Use the repository in three layers:

- `Core`
  The baseline most internal APIs should start with immediately.
- `Extensions`
  Supported capabilities that are common in real services, but not always needed on the first commit.
- `Advanced`
  Heavier platform features for async processing, deeper operations workflows, and more complex runtime setups.

Practical rule:

- start new services with `Core`
- enable `Extensions` when the product has a clear need
- adopt `Advanced` features only when their operational complexity is worth it

## What Belongs In Each Layer

### Core

Core is the smallest set that still feels production-ready for a normal internal API.

Core includes:

- FastAPI app wiring and versioned routers
- request/response schemas
- service/repository separation
- SQLModel models, sessions, and Alembic migrations
- JWT auth with refresh flow
- centralized exception handling and structured logging
- health and readiness endpoints
- Docker dev/prod-like runtime flow
- tests, lint, and type-check setup
- API docs and onboarding docs

If a team only uses Core, they should still have:

- clear boundaries
- deployable application shape
- predictable schema migrations
- basic observability
- stable auth and error handling

### Extensions

Extensions are useful and supported, but they should feel optional from a product-adoption point of view.

Extensions include:

- cache layer
- Prometheus metrics
- Grafana/Prometheus/Alertmanager examples
- provider adapters for email and webhook delivery
- production-oriented auth rate limiting
- richer deployment guidance and security guidance

These features are valuable, but many teams can ship an internal API without turning all of them on immediately.

### Advanced

Advanced features usually imply extra infrastructure, extra operational load, or extra documentation needs.

Advanced includes:

- background worker
- transactional outbox
- retry and dead-letter queues
- outbox dispatcher
- DLQ replay tooling
- operations endpoints and maintenance jobs
- Kubernetes deployment baselines

These are strong platform features, but they should be treated as capabilities to opt into, not assumptions every service must understand on day one.

## Suggested Adoption Path

For a new internal API, the recommended path is:

1. Adopt Core only.
2. Add Extensions after the first real runtime need appears.
3. Add Advanced features only when synchronous request handling is no longer enough.

Examples:

- If the service only does CRUD over Postgres, stay mostly in Core.
- If the service has read-heavy list endpoints, add the cache Extension.
- If the service needs dashboards and alerting, add the monitoring Extension.
- If the service needs async email, webhook fanout, or non-blocking integrations, move into Advanced with worker + outbox.

## Repo Map By Layer

The lists below are meant to help a team decide what to learn first and what can wait.

### Core: Main Application And API Surface

- [app/main.py](/Users/pluto/Documents/git/fastapi101/app/main.py)
  App assembly, middleware, health endpoints, and centralized exception handling.
- [app/api](/Users/pluto/Documents/git/fastapi101/app/api)
  HTTP layer, dependencies, router assembly, and API error mapping.
- [app/services](/Users/pluto/Documents/git/fastapi101/app/services)
  Business logic, service result pattern, and domain-level orchestration.
- [app/db](/Users/pluto/Documents/git/fastapi101/app/db)
  DB session management, SQLModel models, repositories, and Alembic metadata registration.
- [app/schemas](/Users/pluto/Documents/git/fastapi101/app/schemas)
  Public request/response contracts.
- [app/core/config.py](/Users/pluto/Documents/git/fastapi101/app/core/config.py)
  Settings model and environment loading.
- [app/core/security.py](/Users/pluto/Documents/git/fastapi101/app/core/security.py)
  Password hashing and token encoding/decoding.
- [app/core/exceptions.py](/Users/pluto/Documents/git/fastapi101/app/core/exceptions.py)
  App-level exception types.
- [app/core/logging.py](/Users/pluto/Documents/git/fastapi101/app/core/logging.py)
  Structured logging and audit helpers.
- [app/core/health.py](/Users/pluto/Documents/git/fastapi101/app/core/health.py)
  Health/readiness evaluation.
- [alembic](/Users/pluto/Documents/git/fastapi101/alembic)
  Schema migration environment and version history.
- [Dockerfile](/Users/pluto/Documents/git/fastapi101/Dockerfile)
  Application image build.
- [docker-compose.yml](/Users/pluto/Documents/git/fastapi101/docker-compose.yml)
  Production-like local runtime baseline.
- [docker-compose.dev.yml](/Users/pluto/Documents/git/fastapi101/docker-compose.dev.yml)
  Development override with bind mounts and reload flow.
- [tests](/Users/pluto/Documents/git/fastapi101/tests)
  Unit and integration tests across the core architecture.

### Core: Docs

- [README.md](/Users/pluto/Documents/git/fastapi101/README.md)
- [docs/architecture.md](/Users/pluto/Documents/git/fastapi101/docs/architecture.md)
- [docs/api-guide.md](/Users/pluto/Documents/git/fastapi101/docs/api-guide.md)
- [docs/api-contracts.md](/Users/pluto/Documents/git/fastapi101/docs/api-contracts.md)
- [docs/api-recipes.md](/Users/pluto/Documents/git/fastapi101/docs/api-recipes.md)
- [docs/auth-for-clients.md](/Users/pluto/Documents/git/fastapi101/docs/auth-for-clients.md)
- [docs/openapi.md](/Users/pluto/Documents/git/fastapi101/docs/openapi.md)
- [docs/error-codes.md](/Users/pluto/Documents/git/fastapi101/docs/error-codes.md)
- [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md)
- [docs/development.md](/Users/pluto/Documents/git/fastapi101/docs/development.md)

### Extensions: Runtime Capabilities

- [app/core/cache.py](/Users/pluto/Documents/git/fastapi101/app/core/cache.py)
  Shared cache backends and read-through helper.
- [app/core/metrics.py](/Users/pluto/Documents/git/fastapi101/app/core/metrics.py)
  Prometheus metrics registry and app/business metrics.
- [app/core/rate_limit.py](/Users/pluto/Documents/git/fastapi101/app/core/rate_limit.py)
  Auth-focused rate limiting with production Redis option.
- [app/core/resilience.py](/Users/pluto/Documents/git/fastapi101/app/core/resilience.py)
  Timeout/retry policy selection for external dependencies.
- [app/core/telemetry.py](/Users/pluto/Documents/git/fastapi101/app/core/telemetry.py)
  OpenTelemetry setup hooks.
- [app/providers](/Users/pluto/Documents/git/fastapi101/app/providers)
  Email and webhook provider adapters.
- [app/services/email_service.py](/Users/pluto/Documents/git/fastapi101/app/services/email_service.py)
  Email delivery orchestration on top of provider adapters.
- [app/services/webhook_service.py](/Users/pluto/Documents/git/fastapi101/app/services/webhook_service.py)
  Webhook delivery orchestration on top of provider adapters.

### Extensions: Docs And Deployment Examples

- [docs/security.md](/Users/pluto/Documents/git/fastapi101/docs/security.md)
- [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)
- [deploy/monitoring](/Users/pluto/Documents/git/fastapi101/deploy/monitoring)
  Prometheus, Grafana, and Alertmanager examples.
- [docker-compose.monitoring.yml](/Users/pluto/Documents/git/fastapi101/docker-compose.monitoring.yml)
  Local monitoring stack example.

### Advanced: Async And Operations Platform Features

- [app/worker](/Users/pluto/Documents/git/fastapi101/app/worker)
  Typed task envelopes, publishers, runner, idempotency, task handlers, and outbox builders.
- [app/jobs](/Users/pluto/Documents/git/fastapi101/app/jobs)
  Outbox dispatch, revoked-token cleanup, DLQ replay, and outbox reporting jobs.
- [app/db/models/outbox_event.py](/Users/pluto/Documents/git/fastapi101/app/db/models/outbox_event.py)
  Transactional outbox persistence model.
- [app/db/repositories/outbox_event.py](/Users/pluto/Documents/git/fastapi101/app/db/repositories/outbox_event.py)
  Outbox persistence and polling logic.
- [app/services/outbox_service.py](/Users/pluto/Documents/git/fastapi101/app/services/outbox_service.py)
  Operations-facing outbox summary and query logic.
- [app/api/v1/ops.py](/Users/pluto/Documents/git/fastapi101/app/api/v1/ops.py)
  Protected operations API for outbox visibility and replay actions.
- [deploy/kubernetes](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes)
  Kubernetes baseline manifests for app, worker, outbox dispatcher, ingress, HPA, network policy, and maintenance jobs.
- [deploy/nginx/nginx.conf](/Users/pluto/Documents/git/fastapi101/deploy/nginx/nginx.conf)
  Reverse-proxy sample for production deployments.

### Advanced: Docs

- [docs/operations.md](/Users/pluto/Documents/git/fastapi101/docs/operations.md)
  Runbooks, maintenance tasks, and operational caveats for the async/ops side of the platform.

## How Teams Should Read The Repo

For a team starting a new service:

1. Read [README.md](/Users/pluto/Documents/git/fastapi101/README.md).
2. Read [docs/architecture.md](/Users/pluto/Documents/git/fastapi101/docs/architecture.md), [docs/api-guide.md](/Users/pluto/Documents/git/fastapi101/docs/api-guide.md), and [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md).
3. Ignore most of `Extensions` and `Advanced` until a real need appears.

For a team enabling new platform capabilities:

- add cache/metrics/rate limiting from the `Extensions` layer first
- adopt worker/outbox/ops endpoints from the `Advanced` layer only when async processing becomes a product requirement

## Recommendation For This Starter

This repository is no longer a tiny boilerplate, and that is okay.

Treat it as a shared internal platform starter with:

- a strong Core that nearly every service should use
- Extensions that are supported and documented
- Advanced capabilities that are available without forcing every team to learn them immediately

That framing keeps the repository useful without pretending every feature belongs in every service from day one.

## Adoption Checklists

Use [docs/adoption-checklists.md](/Users/pluto/Documents/git/fastapi101/docs/adoption-checklists.md) as the practical rollout guide:

- `Core Only` for teams starting a straightforward internal API
- `Core + Extensions` for teams adding caching, metrics, richer security, or providers
- `Core + Extensions + Advanced` for teams adopting worker, outbox, and operations workflows
