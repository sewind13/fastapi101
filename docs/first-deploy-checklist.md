# First Deploy Checklist

Use this checklist before the first real shared-environment or production-like deployment.

## Configuration And Secrets

- [ ] `SECURITY__SECRET_KEY` replaced with a real secret
- [ ] `DATABASE__URL` points at the real target database
- [ ] `APP__PUBLIC_BASE_URL` is correct for the environment
- [ ] `SECURITY__ISSUER` and `SECURITY__AUDIENCE` are product-specific
- [ ] `API__CORS_ORIGINS` is restricted to real client origins
- [ ] secret values come from a secret manager or controlled platform secret store

## Database And Migrations

- [ ] Alembic migrations are up to date
- [ ] migration strategy is decided:
  migration job, init job, or release step
- [ ] a restore-tested Postgres backup plan exists
- [ ] the team knows who owns database recovery

## Runtime Topology

- [ ] API runs separately from worker processes
- [ ] outbox dispatcher runs separately when async flows are enabled
- [ ] Redis topology is decided for rate limiting, cache, and idempotency
- [ ] broker topology is decided when worker features are enabled
- [ ] ingress or reverse proxy is in place for public traffic

## Observability

- [ ] metrics are enabled or intentionally deferred
- [ ] logs are shipped to a central sink
- [ ] readiness and liveness probes are wired correctly
- [ ] alert routes go to a real human-owned destination
- [ ] dashboards cover API, worker, and dependency health

## Security Hardening

- [ ] public registration is intentionally enabled or disabled
- [ ] ops endpoints are restricted to privileged roles
- [ ] `/metrics` is protected by auth or internal-only routing
- [ ] trusted proxy headers are disabled unless proxy CIDRs are configured
- [ ] no local sample credentials remain in manifests or runtime config

## Release And Rollback

- [ ] build artifact is immutable and versioned
- [ ] release process runs migrations before traffic cutover
- [ ] rollback plan is documented
- [ ] the team understands the difference between app rollback and DB restore

## Smoke Checks After Deploy

- [ ] `/health/live` returns success
- [ ] `/health/ready` returns success
- [ ] login works
- [ ] one protected route works
- [ ] worker processing works if enabled
- [ ] outbox publishing works if enabled
- [ ] metrics scraping works
