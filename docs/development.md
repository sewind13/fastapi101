# Development Guide

This guide covers day-to-day local work: starting the stack, running tests, and adding new features.

## Local Stack

Start the development stack with:

```bash
make up
```

This uses:

- `docker-compose.yml` as the production-like base
- `docker-compose.dev.yml` as the development override

The development stack runs:

- `db`: Postgres
- `web`: FastAPI with source mounted from your workspace
- optional `queue` + `worker` services when using the worker profile

The web container:

- mounts local source into `/app`
- keeps `.venv` in a named Docker volume so the bind mount does not wipe it
- loads env values from `.env`
- overrides `DATABASE__URL` to point at the compose `db` service
- starts through [`scripts/start-dev.sh`](../scripts/start-dev.sh)

Startup flow:

```bash
uv sync --frozen
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Useful commands:

```bash
make up
make down
make ps
make logs
make shell-web
make psql-web
make up-worker
make down-worker
make logs-worker
make bootstrap-admin-in-container
make bootstrap-admin-in-container-env
make replay-dlq
make report-outbox
make cleanup-revoked-tokens
make up-redis
make down-redis
make ps-redis
make logs-redis
```

If you are changing tables or columns, read [docs/database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs/database-migrations.md) first. That file is the dedicated step-by-step guide for schema changes and local DB troubleshooting.

Container-oriented helpers:

- `make shell-web`
  Opens a shell inside the running `web` container.

- `make psql-web`
  Prints the `DATABASE__URL` seen from inside the `web` container. This is useful when local config and compose overrides are confusing.

- `make bootstrap-admin-in-container args="..."`
  Runs the bootstrap admin job inside the `web` container and is the safest choice when your stack is using compose-managed Postgres.

- `make bootstrap-admin-in-container-env args="..."`
  Same as above, but intended for use with `BOOTSTRAP_ADMIN_PASSWORD`.

## Optional Redis Profile

The repository now includes an optional `redis` compose profile for local cache, auth rate limiting, worker idempotency, or health-check experiments.

Start the normal development stack plus Redis with:

```bash
make up-redis
```

Useful helpers:

```bash
make ps-redis
make logs-redis
make down-redis
```

Recommended env values when you want the app containers to talk to the compose-managed Redis service:

```env
CACHE__ENABLED="true"
CACHE__BACKEND="redis"
CACHE__REDIS_URL="redis://redis:6379/2"
AUTH_RATE_LIMIT__BACKEND="redis"
AUTH_RATE_LIMIT__REDIS_URL="redis://redis:6379/0"
WORKER__IDEMPOTENCY_BACKEND="redis"
WORKER__IDEMPOTENCY_REDIS_URL="redis://redis:6379/1"
HEALTH__ENABLE_REDIS_CHECK="true"
HEALTH__REDIS_URL="redis://redis:6379/0"
```

What each block does:

- `CACHE__*`
  Turns on application read cache and stores cached values in Redis instead of per-process memory.
- `AUTH_RATE_LIMIT__*`
  Stores auth rate-limit counters in Redis so multiple app instances share the same login and token-throttling state.
- `WORKER__IDEMPOTENCY_*`
  Stores worker idempotency keys in Redis so retries or duplicate deliveries can be de-duplicated across processes.
- `HEALTH__*`
  Makes the readiness check ping Redis so the app can report when that dependency is unavailable.

Why the sample URLs use different Redis database numbers:

- `/0`
  Auth rate limiting and the Redis health check.
- `/1`
  Worker idempotency keys.
- `/2`
  Application cache entries.

This separation is optional, but it keeps local debugging and key inspection much easier.

If you prefer an external or managed Redis instance instead of the compose profile, keep the same backends but point the URLs at that service. For example, Docker Desktop users commonly use `redis://host.docker.internal:6379/0` when Redis runs outside the compose network.

Recommended split:

- local development: compose Redis profile is fine
- shared or production-like environments: prefer an external or managed Redis service

### Example `.env` Profiles

If you want a copy-friendly starting point, these three profiles cover the most common local setups.

#### 1. No Redis

Use this when you want the simplest local stack and do not need distributed cache, distributed auth rate limiting, or Redis-backed worker idempotency.

```env
CACHE__ENABLED="false"
CACHE__BACKEND="memory"

AUTH_RATE_LIMIT__ENABLED="true"
AUTH_RATE_LIMIT__BACKEND="memory"

WORKER__IDEMPOTENCY_ENABLED="true"
WORKER__IDEMPOTENCY_BACKEND="memory"

HEALTH__ENABLE_REDIS_CHECK="false"
```

#### 2. Cache Only

Use this when you only want to test Redis-backed application cache and keep the rest of the system on in-process defaults.

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

#### 3. Full Redis Setup

Use this when you want all Redis-backed examples turned on in local development.

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

## Background Worker

The template includes an optional AMQP worker profile.

Start it locally with:

```bash
make up-worker
```

This starts:

- `queue`: RabbitMQ
- `worker`: the background worker process
- `outbox-dispatcher`: publishes committed outbox events to the broker
- plus the normal `db` and `web` services

Current example task:

- `user.registered`
- `email.send_welcome`
- `webhook.user_registered`

These tasks are published after successful user registration and consumed by the worker through the shared durable queue configured with `WORKER__*`.

The worker now applies:

- exponential backoff retries through the retry queue
- dead-letter routing after retry exhaustion
- task-id-based idempotency protection

The API no longer needs to publish broker messages directly for the user-registration example. It writes outbox rows in the same DB transaction, and the dispatcher sends them to the broker asynchronously.

## Test Layout

Tests are split by intent:

- `tests/unit/core`: helpers, middleware, config, health, and security logic
- `tests/unit/repositories`: persistence behavior
- `tests/unit/services`: service-level behavior
- `tests/integration/api`: FastAPI route behavior across layers
- `tests/integration/postgres`: Postgres-backed integration tests with transaction-per-test rollback

Run everything:

```bash
uv run pytest -q
```

Run Postgres-marked tests explicitly:

```bash
TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app uv run pytest -m postgres
```

## Load Testing

Load-test guidance and ready-to-run k6 scripts live in [docs/load-testing.md](/Users/pluto/Documents/git/fastapi101/docs/load-testing.md) and [loadtests/k6](/Users/pluto/Documents/git/fastapi101/loadtests/k6).

Recommended local sequence:

```bash
make up-loadtest
make loadtest-smoke
make loadtest-read
```

If you want to test async behavior too:

```bash
make up-loadtest-worker
make loadtest-write
```

## Quality Checks

Run these before pushing changes:

```bash
make lint
make format
make typecheck
uv run pytest -q
```

Install local hooks once per clone:

```bash
uv sync --frozen --all-groups
pre-commit install
```

This repository also includes GitHub Actions CI in [../.github/workflows/ci.yml](../.github/workflows/ci.yml) so the same checks run again on push and pull request.

## Adding A New Feature Slice

The preferred pattern is a full vertical slice:

```mermaid
flowchart LR
    Schema["Schemas"] --> Model["Models"]
    Model --> Repo["Repositories"]
    Repo --> Service["Services"]
    Service --> Route["Routes"]
    Route --> Router["Router registration"]
    Model --> Migration["Alembic migration"]
    Migration --> Tests["Tests"]
    Router --> Tests
```

Typical file touch points:

- `app/schemas/<feature>.py`
- `app/db/models/<feature>.py`
- `app/db/repositories/<feature>.py`
- `app/services/<feature>_service.py`
- `app/api/v1/<feature>.py`
- `app/api/v1/router.py`
- `alembic/versions/*.py`
- relevant tests under `tests/unit` and `tests/integration`

For schema work, pair this section with:

- [docs/database-schema.md](/Users/pluto/Documents/git/fastapi101/docs/database-schema.md)
- [docs/database-migrations.md](/Users/pluto/Documents/git/fastapi101/docs/database-migrations.md)

Operations endpoints are available under `/api/v1/ops/*` and require an authenticated user whose `role` grants platform operations access, such as `ops_admin` or `platform_admin`.

## Removing The Example `items` Module

If you do not want the sample module:

1. Set `EXAMPLES__ENABLE_ITEMS_MODULE="false"` in `.env`.
2. Delete `app/api/v1/items.py`.
3. Delete `app/services/item_service.py`.
4. Delete `app/db/repositories/item.py`.
5. Delete `app/db/models/item.py`.
6. Delete `app/schemas/item.py`.
7. Remove item-related imports and router wiring from `app/api/v1/router.py`, `app/db/models/__init__.py`, `app/db/base.py`, and any package `__init__` files that re-export it.
8. Replace the initial migration with one that matches your real schema, or create a clean new initial migration before the first deploy.
9. Delete item-related tests.
10. Re-run lint, typecheck, and tests.
