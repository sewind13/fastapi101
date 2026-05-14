# Agent Guide

This file is for coding agents and maintainers making changes in this repository.
Use it as the fast guardrail layer before reading the deeper docs.

## Change Scope And Git Safety

- Check the working tree before broad edits when possible.
- Do not revert, overwrite, or clean up unrelated changes unless the user explicitly asks.
- Keep changes scoped to the requested behavior and nearby supporting files.
- Avoid broad refactors while fixing a narrow bug.
- If you find unrelated issues, mention them separately instead of folding them into the current patch.
- Prefer additive compatibility when changing template-facing APIs, imports, env names, or docs.

## Project Shape

- `app/main.py` is the production ASGI entrypoint. Keep it thin and target it as `app.main:app`.
- `app/factory.py` assembles the FastAPI app for runtime and tests.
- `app/api` owns HTTP concerns: routes, dependencies, error mapping, health, metrics, and exception handlers.
- `app/services` owns business rules and orchestration.
- `app/db` owns sessions, models, repositories, and Alembic metadata discovery.
- `app/schemas` owns request and response contracts.
- `app/core/settings` is the settings source of truth.
- `app/core/config.py` is a compatibility shim for existing imports.
- `app/core` owns cross-cutting runtime infrastructure: security, logging, middleware, metrics, telemetry, cache, resilience, and health checks.
- `app/worker` and `app/jobs` are optional advanced runtime capabilities for async tasks, outbox dispatch, maintenance, and DLQ operations.

Read [docs/architecture.md](docs/architecture.md) before changing boundaries.

## Layering Rules

- Routes should stay thin: parse input, resolve dependencies, call services, and return `unwrap_result(...)`.
- Services should not import FastAPI response types or raise `HTTPException`.
- Services should return `ServiceResult` for expected domain outcomes.
- Repositories should own persistence details and should not know about HTTP, auth dependencies, or request state.
- Schemas define the external API contract. Do not expose database models directly as API contracts.
- App assembly files should remain declarative. Do not put business rules in `app/main.py`, `app/factory.py`, middleware registration, health routers, or exception handler registration.

Preferred feature flow:

```text
schema -> model/repository -> service -> route -> router -> tests -> docs
```

## API Patterns

- Add versioned endpoints under `app/api/v1`.
- Register new routers in `app/api/v1/router.py`.
- Put shared request dependencies in `app/api/deps.py`.
- Add or reuse API error mappings in `app/api/errors.py`.
- Add stable service error codes in `app/services/exceptions.py`.
- Keep response bodies consistent with [docs/api-contracts.md](docs/api-contracts.md).
- If a new endpoint changes a public or team-facing contract, update docs.

## Settings And Runtime Config

- New settings belong in the relevant module under `app/core/settings`.
- Use nested env variables such as `SECURITY__SECRET_KEY` and `DATABASE__URL`.
- Keep `app/core/config.py` as a compatibility layer; do not move new settings logic there.
- Production-like safety checks belong in `app/core/settings/validation.py`.
- Optional runtime dependencies must match the feature being enabled:
  - Redis-backed cache, rate limit, idempotency, or Redis readiness checks need `fastapi101[redis]`.
  - AMQP worker, queue health checks, outbox dispatch, or DLQ replay need `fastapi101[worker]`.
  - SES or S3 checks need `fastapi101[aws]`.
  - OpenTelemetry runtime instrumentation needs `fastapi101[observability]`.

Read [docs/configuration.md](docs/configuration.md) before changing env behavior.

## Database And Alembic

- Alembic is the schema source of truth.
- Do not call `create_all()` from application startup.
- Add models under `app/db/models` and ensure Alembic can discover metadata through `app/db/base.py`.
- Add persistence operations under `app/db/repositories`.
- Generate migrations with Alembic, then review them manually.
- `alembic/versions` is intentionally excluded from Ruff lint/format to reduce migration-history churn.
- Do not rewrite old migration files unless the task explicitly requires repairing migration history.

Read [docs/database-migrations.md](docs/database-migrations.md) before changing schema.

## Tests

- Use `create_app()` from `app.factory` for app-instance tests.
- Do not import `app.main` in tests unless the test is specifically checking the runtime entrypoint.
- Unit tests live under `tests/unit`.
- HTTP integration tests live under `tests/integration/api`.
- Postgres-backed integration tests live under `tests/integration/postgres` and are marked separately.
- When changing services, prefer focused service tests plus route tests for API contract behavior.
- When changing repositories or DB behavior, include repository or integration coverage.
- When changing config validation, cover both valid and failing production-like cases.

## Quality Gates

Run these before handing off substantial changes:

```bash
uv run ruff format --check .
uv run ruff check .
UV_CACHE_DIR=.uv-cache uv run mypy app tests
uv run pytest -q
```

For Docker/runtime confidence, also run:

```bash
docker build --tag fastapi-template:ci .
docker run --rm fastapi-template:ci python -c "from app.main import app; print(app.title)"
```

Use the repository's existing `make` targets when that is more convenient.

## Documentation Rules

- English docs live in `docs`.
- Thai docs live in `docs-thai`.
- If you change an English doc that has a Thai counterpart, sync the Thai doc in the same change.
- If behavior, config, commands, API contracts, deployment shape, or production guidance changes, update the relevant English and Thai docs together.
- If you add a new production-facing behavior, update README or the relevant docs map.
- Keep `AGENTS.md` concise. Link to deeper docs instead of duplicating them.

## Security And Production Guardrails

- Never leave sample secrets in production-like config.
- Do not weaken startup validation to make tests pass.
- Metrics and ops endpoints are privileged surfaces; keep auth/network controls explicit.
- Be careful with proxy trust settings. Only trust forwarded headers when trusted proxy CIDRs are configured correctly.
- In multi-instance environments, prefer Redis-backed rate limiting and idempotency over in-memory state.
- Keep webhook target guardrails strict unless a product requirement justifies changing them.

Read [docs/security-hardening.md](docs/security-hardening.md) and [docs/first-deploy-checklist.md](docs/first-deploy-checklist.md) before production-facing changes.

## Worker, Outbox, And Providers

- Use the transactional outbox for side effects that should not block request success.
- Do not publish broker messages directly from request handlers when an outbox flow is appropriate.
- Worker task definitions belong in `app/worker/tasks.py`.
- AMQP publishing and runner behavior belongs in `app/worker`.
- Maintenance and replay commands belong in `app/jobs`.
- Provider adapters belong in `app/providers`.
- Keep provider calls behind timeouts, retries, and dry-run safety where applicable.

Read [docs/operations.md](docs/operations.md) before changing outbox, DLQ, or operational workflows.

## Template Hygiene

- This is a production-grade template, not a product-specific app. Avoid adding product-specific features to the base template.
- Keep optional capabilities opt-in.
- Prefer small, vertical changes over broad refactors.
- Preserve compatibility shims unless there is an explicit migration plan.
- Do not remove the sample `items` module casually; it is the reference feature slice and entitlement example.
- If a change affects generated adopters, update [docs/versioning.md](docs/versioning.md) or release notes.

## Release Or Template Freeze Checklist

Before tagging or freezing a reusable template baseline:

- Run the full quality gates from this file.
- Run Docker build and import smoke checks.
- Confirm English and Thai docs are synced for changed behavior.
- Confirm `.env.*.example` files do not contain real secrets and still match settings.
- Confirm new migrations have been manually reviewed.
- Confirm optional dependencies are still opt-in unless they are core runtime requirements.
- Confirm `app.main:app` imports successfully.
- Record adopter-facing changes in versioning notes or release notes.

## Quick Links

- [README.md](README.md)
- [docs/platform-starter.md](docs/platform-starter.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/api-guide.md](docs/api-guide.md)
- [docs/configuration.md](docs/configuration.md)
- [docs/database-migrations.md](docs/database-migrations.md)
- [docs/security-hardening.md](docs/security-hardening.md)
- [docs/development.md](docs/development.md)
