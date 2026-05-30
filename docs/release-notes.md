# Release Notes

## v1.0.7 - 2026-05-30

Patch release for adopter-facing package and branding documentation cleanup.

### Fixes

- Replaced hard-coded template package extra examples with adopter placeholders such as `<your-package>[redis]`.
- Replaced branded Docker image examples in configuration docs with `ghcr.io/your-org/your-api` placeholders.
- Updated configuration quick-reference defaults for product-facing names, issuer, audience, and telemetry service name to placeholder values.
- Bumped the package, lockfile, Helm chart/app versions, and immutable example image tags to `1.0.7`.

### Adopter Action Items

- Prefer `v1.0.7` for new adopters.
- During adoption, rename the package and product-facing config examples before publishing internal docs.

## v1.0.6 - 2026-05-30

Patch release for final workflow and documentation review comments.

### Fixes

- Updated the Helm values validator to avoid importing through the compatibility config shim and to validate under the Helm values environment overlay.
- Made generic, AKS, and GKE release workflow examples fail on worker and outbox dispatcher rollout failures instead of swallowing them.
- Replaced stale Docker volume reset commands with a Compose-managed `down --volumes` flow that works after adopters rename the repository.
- Updated the production Helm example secret placeholder so it satisfies startup validation while still being clearly replaceable.
- Bumped the package, lockfile, Helm chart/app versions, and immutable example image tags to `1.0.6`.

### Adopter Action Items

- Prefer `v1.0.6` for new adopters.
- If you copied a release workflow from an earlier tag, remove `|| true` from worker/outbox rollout waits unless you intentionally make those workloads optional.

## v1.0.5 - 2026-05-30

Patch release for workflow example parity with Helm startup validation.

### Fixes

- Added Helm values startup validation to `helm-validate-example.yml`.
- Added a `validate_helm_values` preflight job to generic, AKS, EKS, and GKE release workflow examples before migration/deploy.
- Bumped the package, lockfile, Helm chart/app versions, and immutable example image tags to `1.0.5`.

### Adopter Action Items

- Prefer `v1.0.5` for new adopters.
- If you copied a release workflow from an earlier tag, add the Helm values startup validation step before migration/deploy.

## v1.0.4 - 2026-05-30

Patch release for adopter-facing documentation hygiene.

### Fixes

- Replaced local absolute Markdown link targets such as `/Users/.../fastapi101/...` with repository-relative links across English and Thai docs.
- Kept template documentation portable after adopters clone or rename the repository.
- Bumped the package, lockfile, and Helm chart/app versions to `1.0.4`.

### Adopter Action Items

- Prefer `v1.0.4` for new adopters.
- If you forked an earlier release, search your copied docs for local absolute paths before handing them to your team.

## v1.0.3 - 2026-05-30

Patch release for production-readiness quality gates and immutable deployment examples.

### Fixes

- Added `types-pyyaml` to dev dependencies so `uv run mypy app tests` passes with the repository's documented quality gate.
- Updated the Helm values settings validation test typing so mypy accepts the intentional `_env_file=None` runtime override.
- Replaced mutable `latest` image tags in raw Kubernetes manifests and release workflow examples with immutable example tag `1.0.3`.
- Bumped the package, lockfile, and Helm chart/app versions to `1.0.3`.

### Adopter Action Items

- Prefer `v1.0.3` for new adopters.
- Replace the example image repository and immutable tag with your own published product image before deployment.

## v1.0.2 - 2026-05-30

Patch release for Helm release safety and CI coverage.

### Fixes

- Added CI validation that loads bundled Helm values through the application's startup settings validation, not just manifest schema validation.
- Added `scripts/validate_helm_settings.py` so local and CI checks can verify Helm values before release.
- Replaced the default Helm image tag `latest` with immutable example tag `1.0.2`.

### Adopter Action Items

- Prefer `v1.0.2` for new adopters.
- Replace the example image repository and immutable tag with your own published product image before deployment.

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
