# FastAPI Product Template

Production-oriented FastAPI template built for real project starts, not just demos.

## Thai Docs

Thai onboarding and reference docs are available here:

- [README.th.md](README.th.md)
- [docs-thai/README.md](docs-thai/README.md)

If your team works primarily in Thai, start there first and use the English docs as the deeper reference layer.

This repository gives you a layered FastAPI application with:

- versioned API routing
- `BaseSettings`-based configuration
- Postgres + Alembic migrations
- service/repository separation
- JWT auth with refresh rotation and revocation
- structured logging, audit logging, and telemetry hooks
- liveness/readiness endpoints
- optional AMQP-based background worker
- retry and dead-letter queue baseline for background tasks
- worker idempotency and exponential backoff retry baseline
- transactional outbox pattern for broker publishing
- dead-letter queue replay utility for operations
- protected operations API for outbox visibility and DLQ replay
- unit, integration, and Postgres-backed tests
- Docker flows for development and production-like runtime

The `items` module is included as an example feature slice. `POST /api/v1/items/` now also acts as the reference implementation for account-based entitlement enforcement, so adopters can see how quota checks plug into a real route and service flow.

## Platform Layers

This starter is intentionally broader than a minimal boilerplate. To keep it usable, treat it as three layers:

- `Core`: the baseline most internal APIs should start with
- `Extensions`: supported add-ons that many services will want, but not on day one
- `Advanced`: platform features for async workflows, operations, and larger-scale runtime concerns

Start with `Core`, enable `Extensions` when the product needs them, and adopt `Advanced` features only when the operational cost is justified.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Replace `SECURITY__SECRET_KEY` with a strong secret.
3. Set `APP__NAME`, `DATABASE__URL`, `SECURITY__ISSUER`, and `TELEMETRY__SERVICE_NAME`.
4. Decide whether to keep the sample `items` module or set `EXAMPLES__ENABLE_ITEMS_MODULE="false"`.
5. Start the local stack with `make up`.
6. Run checks with `make lint`, `make typecheck`, and `uv run pytest -q`.
7. Export `BOOTSTRAP_ADMIN_PASSWORD` and bootstrap the first privileged operator with `make bootstrap-admin args="--username admin --email admin@example.com"`.

Useful local commands once the stack is running:

```bash
make shell-web
make psql-web
make bootstrap-admin-in-container args="--username admin --email admin@example.com --password 'your-strong-password'"
export BOOTSTRAP_ADMIN_PASSWORD='your-strong-password'
make bootstrap-admin-in-container-env args="--username admin --email admin@example.com"
```

## Docs Map

Start here if you are cloning the template for a new product:

Thai onboarding docs are available in [README.th.md](README.th.md) and [docs-thai/README.md](docs-thai/README.md).

### Core

- [docs/platform-starter.md](docs/platform-starter.md): layer model for this starter and a repo map grouped by `Core`, `Extensions`, and `Advanced`
- [docs/adoption-checklists.md](docs/adoption-checklists.md): practical adoption checklists, a feature decision matrix, and starter profiles for common service shapes
- [docs/architecture.md](docs/architecture.md): layering, boundaries, request flow, and feature-slice structure
- [docs/database-schema.md](docs/database-schema.md): table-level schema map for auth, example data, billing, and outbox domains
- [docs/database-migrations.md](docs/database-migrations.md): step-by-step schema change workflow with Alembic, review guidance, and local troubleshooting
- [docs/api-guide.md](docs/api-guide.md): how to add routes, services, repositories, and resources step by step
- [docs/api-contracts.md](docs/api-contracts.md): success/error response conventions, status codes, and error shapes
- [docs/error-codes.md](docs/error-codes.md): centralized error code catalog with expected status mappings
- [docs/api-recipes.md](docs/api-recipes.md): end-to-end request examples for common API workflows
- [docs/auth-for-clients.md](docs/auth-for-clients.md): how API consumers should log in, refresh, and call protected endpoints
- [docs/billing-entitlements-draft.md](docs/billing-entitlements-draft.md): technical draft for reusable account-based quota and entitlement design
- [docs/configuration.md](docs/configuration.md): environment variables, defaults, and production config notes
- [`.env.min.example`](.env.min.example): minimal starting env set for teams that want the smallest practical baseline
- [docs/bootstrap.md](docs/bootstrap.md): secure day-0/day-1 setup, first-admin bootstrap, and minimum hardening path after cloning
- [docs/secret-management.md](docs/secret-management.md): what should be treated as secrets, where to store them, and how to rotate them safely
- [docs/versioning.md](docs/versioning.md): how to version the template itself and communicate breaking vs non-breaking changes
- [docs/development.md](docs/development.md): local setup, Docker dev flow, testing, and day-to-day commands
- [docs/load-testing.md](docs/load-testing.md): k6 scenarios, load-test matrix, and success criteria for scale testing
- [docs/openapi.md](docs/openapi.md): OpenAPI, Swagger UI, and docs usage

### Extensions

- [docs/security.md](docs/security.md): auth model, token lifecycle, rate limiting, and security hardening guidance
- [docs/deployment.md](docs/deployment.md): production-like Docker flow, migrations, health endpoints, metrics, and deploy notes

### Advanced

- [docs/operations.md](docs/operations.md): maintenance jobs, runbooks, incidents, outbox/DLQ operations, and operational caveats

## Repository Shape

The main directories are best understood by layer:

### Core

- `app/api`: HTTP routes, dependencies, and API error mapping
- `app/services`: business logic and service results
- `app/db`: models, sessions, repositories, and Alembic metadata registration
- `app/schemas`: request/response contracts
- `app/core`: cross-cutting infrastructure such as config, logging, health, auth, telemetry, and rate limiting
- `tests`: unit, integration, and Postgres-backed test suites
- `docs`: project documentation for maintainers and users of the template

### Extensions

- `deploy/monitoring`: Prometheus, Grafana, and Alertmanager examples
- `docker-compose.monitoring.yml`: local monitoring stack example
  Local compose ports are bound to `127.0.0.1` by default for safer development use.

### Advanced

- `app/worker`: background task publisher, task registry, and worker runner
- `app/jobs`: maintenance jobs, the outbox dispatcher, reporting, and replay tools
- `deploy`: deployment examples such as Kubernetes baselines, maintenance jobs, and reverse-proxy config

The full repo-to-layer breakdown is documented in [docs/platform-starter.md](docs/platform-starter.md).

Deployment examples included in the repo:

- Kubernetes config baseline: [`deploy/kubernetes/app-configmap.yaml`](deploy/kubernetes/app-configmap.yaml)
- Kubernetes app baseline: [`deploy/kubernetes/app-deployment.yaml`](deploy/kubernetes/app-deployment.yaml)
- Kubernetes autoscaling baseline: [`deploy/kubernetes/app-hpa.yaml`](deploy/kubernetes/app-hpa.yaml)
- Kubernetes ingress baseline: [`deploy/kubernetes/app-ingress.yaml`](deploy/kubernetes/app-ingress.yaml)
- Kubernetes network policy baseline: [`deploy/kubernetes/app-networkpolicy.yaml`](deploy/kubernetes/app-networkpolicy.yaml)
- Kubernetes worker baseline: [`deploy/kubernetes/worker-deployment.yaml`](deploy/kubernetes/worker-deployment.yaml)
- Kubernetes outbox dispatcher baseline: [`deploy/kubernetes/outbox-dispatcher-deployment.yaml`](deploy/kubernetes/outbox-dispatcher-deployment.yaml)
- Kubernetes secret example: [`deploy/kubernetes/app-secret.example.yaml`](deploy/kubernetes/app-secret.example.yaml)
- Kubernetes kustomize entrypoint: [`deploy/kubernetes/kustomization.yaml`](deploy/kubernetes/kustomization.yaml)
- Cleanup CronJob: [`deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml`](deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml)
- Nginx reverse-proxy sample: [`deploy/nginx/nginx.conf`](deploy/nginx/nginx.conf)

## Template Metadata

This repo includes starter metadata for both templating tools:

- [cookiecutter.json](cookiecutter.json)
- [copier.yml](copier.yml)

Shared placeholders:

- `app_name`
- `db_name`
- `jwt_issuer`
- `service_name`

Suggested mapping:

- `app_name` -> `APP__NAME`
- `db_name` -> database name inside `DATABASE__URL`
- `jwt_issuer` -> `SECURITY__ISSUER`
- `service_name` -> `TELEMETRY__SERVICE_NAME`

## First Things To Edit After Cloning

- rename the project/app to your real product name
- replace `.env` values with environment-specific values
- replace the default JWT secret
- review CORS, readiness, telemetry, and auth-rate-limit settings
- decide whether to keep the sample `items` module
- if you keep `items`, grant `item_create` entitlements before testing `POST /api/v1/items/`
- decide whether your service actually needs the `Extensions` and `Advanced` layers on day one
- add your first real domain module using the same route -> service -> repository -> model -> schema pattern

## Quality Gates

```bash
make lint
make format
make typecheck
uv run pytest -q
```

Automation included in the repo:

- GitHub Actions CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- pre-commit hooks: [`.pre-commit-config.yaml`](.pre-commit-config.yaml)
- License: [`LICENSE`](LICENSE)

## Template Hygiene

- use the included [MIT License](LICENSE) unless your organization needs a different license model
- version the template itself with semantic versioning; see [docs/versioning.md](docs/versioning.md)
- tag stable template releases so adopting teams can record which baseline they started from

## Design Rules

- keep routes thin
- keep services free from HTTP concerns
- keep schemas free from auth/session concerns
- keep Alembic as the schema source of truth
- prefer adding new features as full vertical slices

If you keep those rules, the template stays easier to scale, test, and hand off.

If you want the fastest visual introduction to the database design, start with the ERD in [docs/database-schema.md](docs/database-schema.md).
