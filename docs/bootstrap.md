# Secure Bootstrap Guide

Use this guide the first time a team clones the template for a real product.

The goal is simple:

- get to a running service quickly
- avoid insecure defaults leaking into a shared environment
- bootstrap the first privileged operator safely

## Day-0 Checklist

Before anyone deploys the service, do these in order:

1. Copy `.env.example` to `.env`.
2. Replace `SECURITY__SECRET_KEY` with a real secret from your secret manager.
3. Set product-specific values for:
   - `APP__NAME`
   - `APP__PUBLIC_BASE_URL`
   - `SECURITY__ISSUER`
   - `SECURITY__AUDIENCE`
   - `DATABASE__URL`
4. Set `API__CORS_ORIGINS` to real client origins.
5. Decide whether this product should allow public sign-up through `API__PUBLIC_REGISTRATION_ENABLED`.
6. Decide whether to keep the sample `items` module enabled.
7. If metrics stay enabled, set `METRICS__AUTH_TOKEN`.
8. Choose which platform layers you actually want to enable:
   - `Core`
   - `Extensions`
   - `Advanced`

Related docs:

- [platform-starter.md](./platform-starter.md)
- [adoption-checklists.md](./adoption-checklists.md)
- [configuration.md](./configuration.md)
- [secret-management.md](./secret-management.md)

## Safe Defaults To Review First

These settings are intentionally convenient for local development and should be reviewed before shared environments:

- `API__PUBLIC_REGISTRATION_ENABLED`
- `METRICS__ENABLED`
- `METRICS__AUTH_TOKEN`
- `AUTH_RATE_LIMIT__BACKEND`
- `AUTH_RATE_LIMIT__REDIS_URL`
- `CACHE__BACKEND`
- `CACHE__REDIS_URL`
- `WORKER__ENABLED`
- `WORKER__IDEMPOTENCY_BACKEND`
- `WORKER__IDEMPOTENCY_REDIS_URL`
- `WEBHOOK__ENABLED`
- `EMAIL__ENABLED`

Recommended production-leaning baseline for internal services:

```env
APP__ENV="production"
API__PUBLIC_REGISTRATION_ENABLED="false"
METRICS__ENABLED="false"
METRICS__AUTH_TOKEN="replace-with-real-token"
AUTH_RATE_LIMIT__BACKEND="redis"
CACHE__BACKEND="redis"
WORKER__ENABLED="false"
WEBHOOK__ENABLED="false"
EMAIL__ENABLED="false"
```

Enable extra subsystems only after the owning team is ready to operate them.

If you want Redis locally, this repository now includes an optional compose `redis` profile. That is a good fit for development and smoke testing. For shared or production environments, prefer pointing `*_REDIS_URL` settings at an external or managed Redis service instead of treating compose Redis as long-lived infrastructure.

If you already have an internal Prometheus scrape path and private network controls in place, you can then turn metrics back on and set `METRICS__AUTH_TOKEN`.

## Bootstrap The First Privileged User

Operations endpoints require a privileged user role such as `ops_admin` or `platform_admin`.

Do not bootstrap this by hardcoding usernames in config.

Recommended pattern:

1. Create the user through your normal user-creation flow.
2. Promote that user with the bootstrap command.
3. Disable public registration if the product is internal-only.
4. Verify the privileged user can access `/api/v1/ops/*`.

### Example Bootstrap Flow

If public registration is still enabled in a brand-new environment:

1. Register the first user normally.
2. Promote the user:

```bash
make bootstrap-admin args="--username replace-me --role platform_admin"
```

3. Set `API__PUBLIC_REGISTRATION_ENABLED="false"` if the service should not stay open to public sign-up.

If your product never allows public sign-up, create the first privileged user directly:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin args="--username admin --email admin@example.com --role platform_admin"
```

If your stack is already running through Docker Compose, you can run the same flow inside the `web` container:

```bash
export BOOTSTRAP_ADMIN_PASSWORD='replace-with-a-strong-secret'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com --role platform_admin"
```

Or pass the password directly for one-off local usage:

```bash
make bootstrap-admin-in-container args="--username admin --email admin@example.com --password 'replace-with-a-strong-secret' --role platform_admin"
```

The bootstrap job will:

- create the user if it does not exist yet
- otherwise promote the existing user
- mark the user active by default
- mark the email verified by default

Useful flags:

- `--role ops_admin`
- `--password-env SOME_ENV_VAR`
- `--no-verify-email`
- `--inactive`
- `--phone +66000000000`

### Verification Checklist

After bootstrapping the first admin:

- log in with that user
- confirm `/api/v1/auth/me` works
- confirm `/api/v1/ops/outbox/summary` returns `200`
- confirm a normal `role="user"` account gets `403` for ops endpoints

## Day-1 Hardening

Once the app is running in a shared environment, verify:

- secrets come from a secret manager, not committed files
- metrics are protected by auth and private network routing
- `/health/live` and `/health/ready` are used for different purposes
- Docker compose is treated as local or production-like, not as the final deployment system
- local compose credentials stay local-only and are not copied into shared deployments
- the initial migration matches the real schema after removing sample modules
- CI and pre-commit are enabled for the team

## Team Setup

Recommended team setup after cloning:

```bash
uv sync --frozen --all-groups
pre-commit install
make lint
make typecheck
uv run pytest -q
```

This repository includes:

- GitHub Actions CI in [../.github/workflows/ci.yml](../.github/workflows/ci.yml)
- pre-commit hooks in [../.pre-commit-config.yaml](../.pre-commit-config.yaml)

Useful helper commands:

```bash
make shell-web
make psql-web
```

- `make shell-web` opens a shell inside the running `web` container
- `make psql-web` prints the `DATABASE__URL` seen by the `web` container

## When To Remove The Sample Module

Remove the `items` module before the first real release if:

- it is not part of the product domain
- you do not want demo routes in generated API docs
- you want a clean initial migration that matches only your real schema

If you keep it temporarily, document clearly that it is example-only.
