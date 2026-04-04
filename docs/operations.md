# Operations Guide

This guide covers day-2 concerns: maintenance, incidents, and common operational checks.

For secret ownership, storage, and rotation guidance, see [docs/secret-management.md](/Users/pluto/Documents/git/fastapi101/docs/secret-management.md).

## Scheduled Maintenance

The template ships with a maintenance job for deleting expired rows from `revoked_token`.

Available entrypoints:

- local/dev stack: `make cleanup-revoked-tokens`
- direct process: `python -m app.jobs.cleanup_revoked_tokens`
- shell wrapper: [`scripts/run-cleanup-revoked-tokens.sh`](../scripts/run-cleanup-revoked-tokens.sh)
- Kubernetes example: [`deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml`](../deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml)

Recommended pattern:

- build and publish one application image
- run the API from that image
- run maintenance jobs from the same image with a different command
- pass the same nested env vars through your config and secret system

Suggested schedule:

- hourly is a good default
- every 6-24 hours may be enough for low token churn
- if token churn is high, tighten the schedule instead of cleaning up inline during API requests

## Background Worker Operations

Worker entrypoints:

- direct process: `python -m app.worker.runner`
- Docker dev profile: `make up-worker`
- Docker logs: `make logs-worker`
- outbox logs: `make logs-outbox`
- DLQ replay: `make replay-dlq`
- outbox summary: `make report-outbox`

Protected API endpoints:

- `GET /api/v1/ops/outbox/summary`
- `GET /api/v1/ops/outbox/events`
- `POST /api/v1/ops/outbox/replay-dlq`
- `GET /api/v1/ops/users/{user_id}/auth-state`
- `POST /api/v1/ops/users/{user_id}/unlock`

Useful outbox event filters:

- `status`
- `task_name`
- `task_id`

Example:

- `GET /api/v1/ops/outbox/events?status=failed&task_name=webhook&task_id=abc123`
- `GET /api/v1/ops/users/42/auth-state`

Use the user auth-state endpoints when you need to confirm whether a login problem is caused by account lockout state versus bad credentials, and use the unlock endpoint to clear `failed_login_attempts` and `locked_until` after review.

Operational expectations:

- run the worker as a separate process from the API
- run the outbox dispatcher as a separate process from the API
- use the same image and nested env config as the API
- monitor queue depth and worker failure metrics
- scale workers independently when background throughput increases
- review retry and dead-letter queues regularly
- use Redis-backed idempotency when multiple worker replicas are active

## Common Runbooks

### Readiness Is Failing

1. Check `/health/ready` response details.
2. Confirm `DATABASE__URL` and database reachability.
3. If Redis is enabled, verify `HEALTH__REDIS_URL` and auth/network access.
4. If S3 is enabled, verify `HEALTH__S3_ENDPOINT_URL`, `HEALTH__S3_BUCKET_NAME`, IAM permissions, and region.
5. If queue is enabled, verify `HEALTH__QUEUE_URL`, broker reachability, and credentials.

### Migration Failed During Deploy

1. Inspect migration logs first.
2. Check whether the target database already has partial schema changes.
3. Fix the migration before re-running the app rollout.
4. Avoid falling back to `create_all()` patterns; Alembic must remain the source of truth.

### Cleanup Job Fails

1. Check maintenance logs for `revoked token cleanup failed`.
2. Confirm DB connectivity and credentials.
3. Confirm the job is using the same image and env config as the app.
4. Re-run `python -m app.jobs.cleanup_revoked_tokens` manually if needed.

### Worker Is Not Processing Tasks

1. Confirm `WORKER__ENABLED=true`.
2. Confirm `WORKER__BROKER_URL` is correct for both API and worker.
3. Check broker reachability and queue health.
4. Check worker logs for `background task failed` or connection errors.
5. Check whether tasks are being published at all from the API side.
6. Check retry and dead-letter queue depth metrics.
7. Check whether idempotency state is blocking re-processing unexpectedly.

### Dead-Letter Queue Has Messages

1. Inspect worker logs and identify the failing task type.
2. Fix the root cause first, such as broken webhook config or email provider credentials.
3. Replay a controlled batch from the DLQ with `make replay-dlq`.
4. Watch retry and dead-letter queue depth metrics during replay.
5. If messages fail again immediately, stop replay and investigate further.

Provider-specific hints:

- if `EMAIL__PROVIDER=sendgrid`, verify the API key, categories, and custom args payload shape
- if `EMAIL__PROVIDER=ses`, verify the region, credential mode, and optional configuration set
- if `WEBHOOK__PROVIDER=slack`, verify route mapping in `WEBHOOK__SLACK_ROUTE_URLS` and the fallback webhook URL

### Outbox Is Growing But Queue Stays Empty

1. Check outbox-dispatcher logs first.
2. Confirm broker connectivity from the dispatcher process.
3. Confirm pending rows are being polled from `outbox_event`.
4. Check whether outbox rows are stuck in `failed` status.
5. Run `make report-outbox` to get a quick status summary.

## Logging And Observability Notes

- request logs are structured JSON
- audit logs are separate by logger name
- request IDs are attached to responses and logs
- readiness and maintenance logs should be forwarded to the same log pipeline as the app
- Prometheus metrics are available at the configured metrics path, `/metrics` by default, and may require a bearer token when `METRICS__AUTH_TOKEN` is set
- local monitoring examples include Prometheus, Grafana, and Alertmanager

## Suggested Alerts

Starting points for alerting:

- `5xx rate > 1% for 5m`
  Investigate app exceptions, dependency failures, and rollout issues.

- `p95 latency > 500ms for 10m`
  Investigate DB pressure, external dependency latency, and slow endpoints.

- `high in-flight requests for 5-10m`
  Investigate thread/worker saturation, backpressure, and downstream slowness.

- `database readiness failed for 2m`
  Treat this as high priority because traffic admission should stop.

- `critical external dependency readiness failed for 5m`
  Investigate Redis, queue, or S3 access depending on what your app truly depends on.

- `login failure spike for 10m`
  Investigate attack traffic, credential stuffing, or broken client login behavior.

- `cleanup job failures for 15m`
  Investigate maintenance runner health, DB connectivity, and deployment config drift.

Good Prometheus series to build alerts from:

- `fastapi_template_http_requests_total`
- `fastapi_template_http_request_duration_seconds`
- `fastapi_template_http_requests_in_progress`
- `fastapi_template_app_exceptions_total`
- `fastapi_template_readiness_checks_total`
- `fastapi_template_readiness_dependency_status`
- `fastapi_template_auth_events_total`
- `fastapi_template_maintenance_job_runs_total`
- `fastapi_template_maintenance_job_deleted_total`
- `fastapi_template_worker_events_total`
- `fastapi_template_worker_queue_depth`
- `fastapi_template_outbox_dispatch_events_total`

## Alertmanager Notes

The example Alertmanager config is intentionally a starter:

- webhook receivers point to placeholder local endpoints
- Slack webhook URL is a placeholder
- SMTP settings are placeholders

Before real use:

1. replace webhook URLs
2. replace Slack credentials
3. replace SMTP settings
4. route critical alerts to your real paging system

## Business Metrics To Watch

- rising `auth.failed` with steady traffic
  Could indicate credential stuffing or client-side auth bugs.

- rising `auth.rate_limited`
  Could indicate attack traffic or thresholds that are too tight.

- low or zero `auth.refresh.succeeded` when access traffic is normal
  Could indicate broken refresh flow in clients.

- repeated `maintenance_job_runs_total{outcome="failed"}`
  Could indicate DB access issues or broken maintenance commands.

- repeated `worker_events_total{outcome="failed"}`
  Could indicate a broken task handler, malformed payloads, or broker/consumer instability.

- rising `worker_events_total{outcome="skipped_duplicate"}`
  Could indicate harmless redelivery handling, or an idempotency window that is too aggressive for your workload.

- growing `worker_queue_depth{queue_name=~".*\\.retry"}`
  Could indicate tasks are failing repeatedly and draining slowly.

- non-zero `worker_queue_depth{queue_name=~".*\\.dlq"}`
  Could indicate tasks have exhausted retries and now need manual inspection.

- unusual spikes in `maintenance_job_deleted_total`
  Could indicate unexpected token churn or abnormal auth usage patterns.

## Operational Caveats

- `memory` rate limiting is not distributed
- use the Redis backend for multi-instance deployments
- readiness checks validate client connectivity, not end-to-end business health
- S3 readiness needs valid credentials and bucket access
- queue readiness validates connection establishment, not message throughput or consumer lag
- the included worker is a starter pattern and does not yet include retries, dead-letter routing, or delayed delivery semantics
- the included worker now includes baseline retry, exponential backoff, dead-letter routing, idempotency protection, per-task retry policies, and a transactional outbox, but it still does not include a full outbox-to-broker exactly-once guarantee
