# Release Notes

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
