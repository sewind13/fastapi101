# Template Readiness Tracker

Use this document to track follow-up work that improves this repository as a production-grade FastAPI template.

Recommended status values:

- `todo`
- `in_progress`
- `blocked`
- `done`

Recommended effort values:

- `S`
- `M`
- `L`

## Summary Board

| ID | Priority | Task | Owner | Effort | Status | Target | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TR-001 | P1 | Separate migrations from API startup |  | S | done |  | API startup no longer runs Alembic; docs updated. |
| TR-002 | P1 | Align Helm defaults with production validation rules |  | S | done |  | Helm defaults updated and validated. |
| TR-003 | P1 | Define image and extras strategy for optional runtime features |  | M | done |  | Docker build arg, compose, CI, docs, and image smoke checks completed. |
| TR-004 | P2 | Make metrics exposure more secure by default |  | S | done |  | Metrics default changed to disabled and tests/docs updated. |
| TR-005 | P2 | Harden Docker image for production baselines |  | M | done |  | Dockerfile converted to multi-stage non-root runtime and validated. |
| TR-006 | P2 | Add security and supply-chain checks to CI |  | M | done |  | CI security job, image SBOM/scan, dependency fixes, and audit validation completed. |
| TR-007 | P3 | Split password reset expiry from email verification expiry |  | S | done |  | Dedicated setting, token usage, examples, docs, and tests completed. |
| TR-008 | P3 | Strengthen password policy defaults |  | S | done |  | Default minimum password length raised to 12 with docs/tests updated. |
| TR-009 | P3 | Add clearer adoption profiles and presets |  | M | done |  | Added core-only, redis-enabled, and full-async preset guidance with env/Docker/Helm examples. |

## Detailed Tracking

### TR-001: Separate Migrations From API Startup

- Priority: `P1`
- Owner:
- Effort: `S`
- Status: `done`
- Target date:

Why:

- API startup previously ran migrations in [scripts/start-web.sh](/Users/pluto/Documents/git/fastapi101/scripts/start-web.sh:5).
- Kubernetes and Helm already include a separate migration job in [deploy/kubernetes/migration-job.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/migration-job.yaml:1) and [deploy/helm/fastapi-template/templates/migration-job.yaml](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template/templates/migration-job.yaml:1).

Risks if unchanged:

- concurrent migrations during multi-replica rollout
- API pods require broader DB privileges than necessary
- release flow remains ambiguous

Definition of done:

- [x] `scripts/start-web.sh` starts the API only
- [x] migrations run through job, init step, or release pipeline only
- [x] deployment docs explain the intended migration flow clearly
- [x] Docker and Kubernetes examples match the new flow

Notes:

- Completed initial split on 2026-05-28.

### TR-002: Align Helm Defaults With Production Validation Rules

- Priority: `P1`
- Owner:
- Effort: `S`
- Status: `done`
- Target date:

Why:

- Helm defaults in [deploy/helm/fastapi-template/values.yaml](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template/values.yaml:85) provide a lean production-safe `core-only` setup.
- Validation in [app/core/settings/validation.py](/Users/pluto/Documents/git/fastapi101/app/core/settings/validation.py:85) rejects `API__PUBLIC_REGISTRATION_ENABLED=true` when `OPS__ENABLED=true`.
- Current settings defaults in [app/core/settings/base.py](/Users/pluto/Documents/git/fastapi101/app/core/settings/base.py:17) and [app/core/settings/base.py](/Users/pluto/Documents/git/fastapi101/app/core/settings/base.py:50) can still produce that invalid combination.

Risks if unchanged:

- default chart appears valid but fails at startup
- adopters lose trust in example manifests

Definition of done:

- [x] Helm default values pass startup validation
- [x] default chart configuration reflects secure production intent
- [x] README or deployment docs mention any important default behavior change
- [x] chart validation or smoke coverage catches future drift

Notes:

- Added explicit production-safe Helm defaults for public registration, examples, public base URL, and lean `core-only` adoption. Validated with settings startup, `helm lint`, and `helm template`.

### TR-003: Define Image And Extras Strategy For Optional Runtime Features

- Priority: `P1`
- Owner:
- Effort: `M`
- Status: `done`
- Target date:

Why:

- Optional dependencies are declared in [pyproject.toml](/Users/pluto/Documents/git/fastapi101/pyproject.toml:20).
- The default image in [Dockerfile](/Users/pluto/Documents/git/fastapi101/Dockerfile:16) installs core dependencies only.
- Production examples enable Redis, worker, and telemetry features in [deploy/helm/fastapi-template/values.prod.example.yaml](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template/values.prod.example.yaml:101).

Risks if unchanged:

- runtime import errors when feature flags and image contents diverge
- confusing adoption story for teams choosing between core and advanced capabilities

Definition of done:

- [x] choose a supported strategy: `core` image, `full` image, build arg, or multi-target builds
- [x] docs explain exactly which image supports which features
- [x] Helm and deployment examples reference the intended image strategy
- [x] CI verifies at least the supported image profiles

Notes:

- Added `RUNTIME_EXTRAS` Docker build arg. Default builds the core runtime; `RUNTIME_EXTRAS=all` builds the fully loaded runtime used by worker/Redis/observability deployments. Validated core and full Docker builds plus import smoke checks.

### TR-004: Make Metrics Exposure More Secure By Default

- Priority: `P2`
- Owner:
- Effort: `S`
- Status: `done`
- Target date:

Why:

- Metrics are enabled by default in [app/core/settings/observability.py](/Users/pluto/Documents/git/fastapi101/app/core/settings/observability.py:57).
- The route in [app/api/metrics.py](/Users/pluto/Documents/git/fastapi101/app/api/metrics.py:11) only requires auth when a token is configured.

Risks if unchanged:

- staging or preview environments may expose metrics unintentionally
- adopters may assume metrics are protected when they are only conditionally protected

Definition of done:

- [x] metrics default is reviewed and made explicitly safe
- [x] auth expectations are documented for non-local environments
- [x] test coverage exists for the intended protected behavior

Notes:

- Changed `METRICS__ENABLED` default to `false` and documented explicit opt-in behavior. Validated with config, metrics, and factory tests.

### TR-005: Harden Docker Image For Production Baselines

- Priority: `P2`
- Owner:
- Effort: `M`
- Status: `done`
- Target date:

Why:

- The current image in [Dockerfile](/Users/pluto/Documents/git/fastapi101/Dockerfile:1) is functional but still uses a root runtime and keeps build tooling in the final image.

Risks if unchanged:

- larger runtime image than necessary
- broader attack surface than a stronger platform baseline should carry

Definition of done:

- [x] container runs as non-root
- [x] build dependencies are reduced or removed from the final image
- [x] Docker build and startup smoke checks still pass
- [x] deployment docs mention any operational implications

Notes:

- Converted Dockerfile to a builder/runtime split and added a non-root `app` runtime user. Validated core/full image builds, import smoke checks, optional dependency imports, and runtime Alembic availability.

### TR-006: Add Security And Supply-Chain Checks To CI

- Priority: `P2`
- Owner:
- Effort: `M`
- Status: `done`
- Target date:

Why:

- The CI workflow in [`.github/workflows/ci.yml`](/Users/pluto/Documents/git/fastapi101/.github/workflows/ci.yml:1) already covers quality and deployment validation well.
- It does not yet include baseline security automation such as dependency audit, secret scanning, container scanning, or SBOM generation.

Risks if unchanged:

- weaker organizational baseline for a shared template
- more manual review burden for adopters

Definition of done:

- [x] decide which checks are informational vs merge-blocking
- [x] add at least one dependency or vulnerability scan
- [x] add at least one secret scanning step
- [x] add container scanning or SBOM generation for shipped images

Notes:

- Added blocking Python dependency audit and committed-secret scan. Added informational Trivy image scan and CycloneDX SBOM artifact for the full image.
- The first dependency audit found known vulnerabilities in `idna`, `mako`, `pygments`, `python-multipart`, `starlette`, and `urllib3`; updated [uv.lock](/Users/pluto/Documents/git/fastapi101/uv.lock:1) to fixed versions and re-ran `pip-audit` successfully.

### TR-007: Split Password Reset Expiry From Email Verification Expiry

- Priority: `P3`
- Owner:
- Effort: `S`
- Status: `done`
- Target date:

Why:

- Password reset token creation in [app/core/security.py](/Users/pluto/Documents/git/fastapi101/app/core/security.py:80) currently reuses the email verification expiry setting.

Risks if unchanged:

- password reset policy cannot be tuned independently
- security posture changes in one flow may unintentionally affect another

Definition of done:

- [x] add a dedicated password reset expiry setting
- [x] update token creation to use the new setting
- [x] update tests and config docs

Notes:

- Added `SECURITY__PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` with a 60-minute default. Password reset tokens now use this setting instead of the email-verification token lifetime.

### TR-008: Strengthen Password Policy Defaults

- Priority: `P3`
- Owner:
- Effort: `S`
- Status: `done`
- Target date:

Why:

- Security defaults in [app/core/settings/security.py](/Users/pluto/Documents/git/fastapi101/app/core/settings/security.py:8) are configurable but relatively permissive for a shared production template.

Risks if unchanged:

- adopters who keep defaults may ship a weaker password baseline than intended

Definition of done:

- [x] review desired default password policy for this template
- [x] update docs to explain the chosen defaults and tradeoffs
- [x] verify auth tests still reflect the intended baseline

Notes:

- Chose a length-focused baseline: `SECURITY__PASSWORD_MIN_LENGTH=12` by default, without adding uppercase/digit/special requirements by default.

### TR-009: Add Clearer Adoption Profiles And Presets

- Priority: `P3`
- Owner:
- Effort: `M`
- Status: `done`
- Target date:

Why:

- This repository is closer to a platform starter than a minimal starter.
- Teams would benefit from clearer presets for `core-only`, `redis-enabled`, and `full async` usage patterns.

Risks if unchanged:

- teams may enable too much too early
- onboarding remains more complex than necessary

Definition of done:

- [x] define a small set of supported adoption profiles
- [x] provide matching env, Docker, or Helm examples where useful
- [x] link the profiles from onboarding docs

Notes:

- Added `core-only`, `redis-enabled`, and `full-async` preset quick references to English and Thai adoption docs, with links from platform-starter docs.

## Suggested Execution Order

1. TR-001 Separate migrations from API startup
2. TR-002 Align Helm defaults with production validation rules
3. TR-003 Define image and extras strategy
4. TR-004 Make metrics exposure more secure by default
5. TR-005 Harden Docker image
6. TR-006 Add security and supply-chain checks to CI
7. TR-007 Split password reset expiry
8. TR-008 Strengthen password defaults
9. TR-009 Add clearer adoption profiles and presets

## Review Log

| Date | Reviewer | Summary | Follow-up |
| --- | --- | --- | --- |
| 2026-05-28 | Codex | Initial template readiness review converted into tracker. | Start with TR-001 to TR-003. |
| 2026-05-28 | Codex | Completed TR-001 through TR-009 and validated quality, security, Helm, workflow, and Docker smoke checks. | Review diff and decide whether to stage/commit as one hardening pass or split into smaller commits. |
