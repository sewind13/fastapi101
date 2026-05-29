# Release Notes

## v1.0.1 - 2026-05-30

Patch release for the default Helm chart baseline.

### Fixes

- Fixed `deploy/helm/fastapi-template/values.yaml` so the lean `core-only` Helm defaults pass production settings validation.
- The default chart now disables auth rate limiting when Redis is not enabled. Redis-backed rate limiting remains available through the `redis-enabled` and `full-async` presets.
- Added a unit test that loads the default Helm values into `Settings(_env_file=None)` to prevent future chart/config drift.

### Adopter Action Items

- Prefer `v1.0.1` over `v1.0.0` if using the bundled default Helm values.
- If enabling auth rate limiting in production, set `AUTH_RATE_LIMIT__ENABLED=true`, `AUTH_RATE_LIMIT__BACKEND=redis`, and `AUTH_RATE_LIMIT__REDIS_URL`.

## v1.0.0 - 2026-05-29

First stable production-grade product-template baseline.

### Status

- Stability: stable template baseline
- Breaking changes for existing adopters: none, because this is the first stable release
- Recommended tag: `v1.0.0`

### Highlights

- Production FastAPI application structure with thin routes, service/repository layering, typed schemas, and `app.main:app` as the ASGI entrypoint.
- Typed settings split by domain, production validation, compatibility shims for legacy env names, and documented nested env variables.
- Alembic-first database workflow with migrations decoupled from API startup.
- Hardened Docker runtime with multi-stage builds, optional runtime extras, and non-root execution.
- Helm and Kubernetes deployment baselines, with Helm defaults set to a lean `core-only` profile and `values.prod.example.yaml` kept as the fuller async/Redis/ops example.
- Auth baseline with JWT access/refresh tokens, token revocation, email verification, password reset, account lockout, rate limiting, and password-policy controls.
- Observability and operations surfaces documented as opt-in production capabilities.
- CI quality and supply-chain baseline covering formatting, linting, typing, tests, workflow validation, dependency audit, secret scanning, Docker builds, Trivy image scan, and SBOM generation.
- English and Thai onboarding/reference docs for architecture, configuration, deployment, security, operations, and adoption profiles.

### Adopter Action Items

- Replace all example secrets and URLs before deployment.
- Pick an adoption preset: `core-only`, `redis-enabled`, or `full-async`.
- Decide whether to keep the sample `items` module and entitlement example.
- Run the full quality gates before tagging product-specific forks.
- Record `v1.0.0` as the template baseline for generated products.

### Validation

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy app tests`
- `uv run pytest -q`
- `helm lint deploy/helm/fastapi-template`
- `helm template fastapi-template deploy/helm/fastapi-template`
- `actionlint .github/workflows/ci.yml`
- `pip-audit --no-deps --disable-pip`
- `gitleaks detect`
- Docker core and full image smoke checks
