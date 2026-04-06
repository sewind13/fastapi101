# Secret Management

This guide explains how to treat secrets in this template, where they should live, and how to rotate them safely.

## Goals

Use this guide to keep a clear split between:

- ordinary configuration
- environment-specific but non-secret values
- real secrets that must come from a secret-management system

The template supports nested environment variables, but production deployments should not treat `.env` as the long-term secret source of truth.

For a production-oriented starting point, see [/.env.prod.example](/Users/pluto/Documents/git/fastapi101/.env.prod.example). Use it as an inventory and review aid, not as a committed source of real secrets.

## What Counts As A Secret

In this template, these values should normally be treated as secrets:

- `SECURITY__SECRET_KEY`
- `DATABASE__URL` when it contains credentials
- `AUTH_RATE_LIMIT__REDIS_URL` when it contains credentials
- `CACHE__REDIS_URL` when it contains credentials
- `WORKER__BROKER_URL` when it contains credentials
- `WORKER__IDEMPOTENCY_REDIS_URL` when it contains credentials
- `METRICS__AUTH_TOKEN`
- `EMAIL__PASSWORD`
- `EMAIL__SENDGRID_API_KEY`
- `EMAIL__SES_ACCESS_KEY_ID`
- `EMAIL__SES_SECRET_ACCESS_KEY`
- `EMAIL__SES_SESSION_TOKEN`
- `WEBHOOK__AUTH_HEADER_VALUE`
- `WEBHOOK__SLACK_WEBHOOK_URL`
- any route-specific webhook URLs in `WEBHOOK__SLACK_ROUTE_URLS`

Values that are usually configuration rather than secrets:

- `APP__NAME`
- `APP__ENV`
- `APP__PUBLIC_BASE_URL`
- `API__V1_PREFIX`
- `API__CORS_ORIGINS`
- `SECURITY__ISSUER`
- `SECURITY__AUDIENCE`
- logging, telemetry, and health-check toggles
- password-policy thresholds
- rate-limit thresholds

## Recommended Sources By Environment

### Local Development

Acceptable pattern:

- copy `.env.example` to `.env`
- use fake or local-only secrets
- do not reuse production credentials locally

### Shared Development / Staging

Recommended pattern:

- keep non-secret defaults in ConfigMaps or deployment manifests
- load real secrets from your platform secret store
- avoid committing long-lived shared secrets into the repo

### Production

Recommended pattern:

- store secrets in a secret manager such as Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, or Kubernetes Secrets backed by your platform controls
- inject them at runtime as environment variables or mounted secret files
- keep `.env` out of the production runtime path
- audit who can read or change each secret

## Suggested Secret Inventory

Start with a small, explicit inventory for each service:

| Secret | Typical owner | Rotation priority | Notes |
| --- | --- | --- | --- |
| `SECURITY__SECRET_KEY` | Platform / service owner | High | JWT signing secret |
| DB credentials in `DATABASE__URL` | Platform / database owner | High | Rotate with DB user lifecycle |
| Redis credentials | Platform owner | Medium | Used by rate limit / cache / idempotency depending on setup |
| `WORKER__BROKER_URL` credentials | Platform owner | Medium | Worker and publisher both depend on it |
| `METRICS__AUTH_TOKEN` | Platform owner | Medium | Internal scrape token |
| Email provider credentials | Product / platform owner | High | SendGrid / SES / SMTP auth |
| Webhook auth tokens | Product owner | Medium | Outbound integration secret |

Keep this inventory in your service runbook or platform docs and update it when integrations change.

## Platform Patterns

### Kubernetes

Recommended split:

- ConfigMap for non-secret values
- Secret for credentials, tokens, and private URLs

See:

- [deploy/kubernetes/app-configmap.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-configmap.yaml)
- [deploy/kubernetes/app-secret.example.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-secret.example.yaml)

### Cloud Secret Managers

Common pattern:

1. store each secret in the managed secret service
2. grant the workload identity permission to read only what it needs
3. inject those values into the deployment environment
4. keep product-level config in your deploy system, not in the repo

## Rotation Principles

Good rotation is less about changing a value and more about making sure the system keeps serving while the value changes.

Use these rules:

- rotate one secret class at a time
- prefer dual-read or staged rollout patterns when possible
- document which services depend on the secret before changing it
- verify health, auth, and background jobs after rotation
- never rotate by editing random pods or containers manually

## Rotation Runbooks

### Rotate `SECURITY__SECRET_KEY`

This is the most sensitive rotation because it affects JWT verification.

Current template note:

- the app uses a single active signing key
- rotating it immediately invalidates existing access and refresh tokens

Safe baseline procedure:

1. schedule a maintenance window or announce forced re-authentication.
2. generate a new strong secret.
3. update the secret in your secret manager.
4. roll the application and any services that verify these JWTs.
5. verify login, refresh, and protected routes.
6. monitor `401`, `auth.invalid_token`, and `auth.refresh_reused` spikes.

If you need zero-downtime token-key rotation later, extend the template to support key IDs and multiple verification keys.

### Rotate Database Credentials

1. create new DB credentials first.
2. update the secret store with the new connection string.
3. roll API, worker, dispatcher, and maintenance jobs.
4. verify `/health/ready`, migrations, worker publishing, and maintenance jobs.
5. remove the old DB credentials only after all workloads have moved.

### Rotate Redis / Broker Credentials

1. issue new credentials.
2. update the shared secret source.
3. roll all workloads that use the connection:
   - API
   - worker
   - outbox dispatcher
   - maintenance jobs if applicable
4. verify rate limiting, cache, queue publishing, and worker consumption.
5. remove the old credentials after traffic stabilizes.

### Rotate Email / Webhook Provider Credentials

1. create the replacement credential or webhook secret.
2. update the secret source.
3. roll workloads that send those events.
4. trigger a controlled test message or webhook.
5. verify provider dashboards and application logs.
6. revoke the previous credential.

## After-Rotation Verification Checklist

After any secret rotation, verify at least:

- `/health/live`
- `/health/ready`
- login
- refresh token flow
- one protected endpoint
- worker publishing and consumption if enabled
- outbox dispatcher health if enabled
- email or webhook delivery if that provider secret changed

Also check:

- error rate
- readiness failures
- auth failures
- worker backlog / DLQ depth

## Backup, Restore, And Rollback Story

Production readiness is not only about secret rotation. You also need a clear plan for:

- how data is backed up
- how backups are verified
- how restores are practiced
- how release rollback differs from data recovery

### Backup Scope

At minimum, define backup coverage for:

- Postgres
- Redis, if Redis stores state you cannot tolerate losing
- broker state, if your operational model depends on durable queues
- deployment config and secret inventory metadata

Recommended baseline for this template:

- Postgres backups are mandatory
- Redis backups are optional when Redis is used only for cache
- Redis persistence matters more when it holds shared rate-limit or idempotency state and you care about preserving it across incidents
- broker durability should be handled by your queue platform settings, not assumed by the application

### Postgres Backup Expectations

For production-like use, have a written answer for all of these:

- backup frequency
- retention window
- storage location
- encryption at rest
- restore ownership
- last successful restore rehearsal date

Recommended pattern:

- use managed Postgres backups when available
- also define point-in-time recovery expectations if the platform supports it
- document how to restore into a new instance for validation

### Restore Drill Expectations

Backups are only trustworthy when restore is rehearsed.

At minimum, rehearse:

1. restoring a recent Postgres backup into an isolated environment
2. pointing a copy of the app at that restored database
3. verifying login, one protected route, and one representative business flow
4. confirming Alembic version state is what you expect

Keep a record of:

- backup timestamp used
- restore target environment
- validation steps run
- issues found and follow-up work

### Rollback vs Restore

Treat these as different tools:

- rollback:
  move the application back to a previous working release
- restore:
  recover data or infrastructure state from a backup

Use rollback first when:

- the new app image is bad
- the new worker build is bad
- the migration is forward-compatible and the previous app can still run safely

Use restore when:

- data was corrupted or deleted
- a destructive migration was applied incorrectly
- an infrastructure failure requires state recovery

### Minimum Recovery Runbook

Before calling the template production-ready, document:

1. who can trigger restore actions
2. where backups live
3. what recovery point objective you accept
4. what recovery time objective you accept
5. how to validate a restored environment before sending traffic

## What Not To Do

- do not commit production secrets to the repo
- do not reuse local secrets in shared environments
- do not leave placeholder example secrets in production
- do not rotate JWT signing secrets casually without planning for token invalidation
- do not store secret values in docs, tickets, or chat logs

## Related Docs

- [docs/configuration.md](/Users/pluto/Documents/git/fastapi101/docs/configuration.md)
- [docs/deployment.md](/Users/pluto/Documents/git/fastapi101/docs/deployment.md)
- [docs/operations.md](/Users/pluto/Documents/git/fastapi101/docs/operations.md)
- [docs/security.md](/Users/pluto/Documents/git/fastapi101/docs/security.md)
