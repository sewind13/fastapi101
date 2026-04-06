# Observability Guide

This guide defines the default observability shape that should be turned on when using the template in production-like environments.

## Goals

A production-ready baseline should make it easy to answer:

- is the API healthy
- are dependencies reachable
- are requests failing
- are requests getting slow
- are workers falling behind
- are background tasks failing

## Recommended Defaults

For shared environments and production-like deployments, prefer:

- structured JSON logs enabled
- request IDs propagated in responses and logs
- Prometheus metrics enabled and scraped internally
- readiness probes enabled for true dependencies
- a log sink or aggregator outside the app container
- alerts for error rate, latency, saturation, and queue depth

## Logging

The template already emits:

- structured request logs
- separate audit logs
- request IDs

Recommended production setup:

- ship stdout and stderr to a centralized log pipeline
- index `request_id`, path, status code, and error code
- keep API, worker, and dispatcher logs in the same platform but with clear workload labels

Useful default log fields to preserve:

- timestamp
- level
- request_id
- path
- method
- status_code
- error_code
- worker task name when applicable

## Metrics

Recommended baseline:

- `METRICS__ENABLED=true`
- internal scrape path only
- `METRICS__AUTH_TOKEN` set if app-level auth is used for metrics

Useful baseline metrics already exposed by the template include:

- request totals
- request latency
- in-flight requests
- application exceptions
- readiness dependency status
- auth event counters
- maintenance job counters
- worker events
- queue depth
- outbox dispatch events

## Tracing

If you have an OTLP collector or tracing backend, turn telemetry on early in shared environments:

- `TELEMETRY__ENABLED=true`
- `TELEMETRY__EXPORTER_OTLP_ENDPOINT=...`
- `TELEMETRY__SERVICE_NAME=...`

Recommended baseline:

- start with API traces first
- add worker traces next if async work is important to your product
- make sure request IDs and trace IDs can be correlated in your logs

## Default Alerts

Good production starting points:

- `5xx rate > 1% for 5m`
- `p95 latency > 500ms for 10m`
- high in-flight requests for 5-10m
- database readiness failed for 2m
- Redis readiness failed for 5m when Redis is required
- queue depth growing unexpectedly
- DLQ depth non-zero for more than a short investigation window
- maintenance jobs failing repeatedly

## Workload-Specific Checks

### API

Watch:

- request rate
- error rate
- p95 and p99 latency
- readiness status

### Worker

Watch:

- task failures
- duplicate-skip rate
- retry queue depth
- dead-letter queue depth

### Outbox Dispatcher

Watch:

- dispatch failures
- pending outbox growth
- broker connectivity issues

## Recommended First Production Settings

Suggested baseline:

```env
METRICS__ENABLED="true"
METRICS__PATH="/metrics"
METRICS__AUTH_TOKEN="replace-with-real-token"
TELEMETRY__ENABLED="true"
TELEMETRY__SERVICE_NAME="your-service-name"
TELEMETRY__EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
```

Then confirm:

- Prometheus is scraping successfully
- dashboards show live traffic
- alerts route to a real team destination
- logs can be searched by `request_id`
