# Load Testing Guide

This guide explains how to performance-test the starter in a way that matches the architecture in this repository.

The goal is not to produce a single “magic RPS number.” The goal is to learn:

- where the bottleneck appears first
- how the API behaves under read-heavy, write-heavy, and auth-heavy traffic
- whether async components keep up when worker and outbox are enabled
- whether the service still meets your latency and error-rate targets

## Recommended Test Order

Run load tests in this order:

1. `smoke`
2. `read baseline`
3. `auth burst`
4. `write + async`
5. `soak`

This sequence catches setup issues first, then increases realism and operational stress.

## k6 Scripts Included

The repository includes ready-to-run k6 scenarios in [loadtests/k6](/Users/pluto/Documents/git/fastapi101/loadtests/k6):

- [loadtests/k6/smoke.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/smoke.js)
- [loadtests/k6/read_baseline.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/read_baseline.js)
- [loadtests/k6/auth_burst.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/auth_burst.js)
- [loadtests/k6/write_async.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/write_async.js)
- [loadtests/k6/soak.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/soak.js)
- [loadtests/k6/common.js](/Users/pluto/Documents/git/fastapi101/loadtests/k6/common.js)

These scripts assume the application is reachable at `BASE_URL`, which defaults to `http://localhost:8000`.

## Environment Variables

Useful runtime overrides:

```bash
BASE_URL=http://localhost:8000
USERNAME_PREFIX=k6user
PASSWORD=strongpassword123
ITEMS_ENABLED=true
```

If the example `items` module has been disabled, run with:

```bash
ITEMS_ENABLED=false
```

## Example Commands

If `k6` is installed locally:

```bash
k6 run loadtests/k6/smoke.js
k6 run loadtests/k6/read_baseline.js
k6 run loadtests/k6/auth_burst.js
k6 run loadtests/k6/write_async.js
k6 run loadtests/k6/soak.js
```

Recommended local stack before running:

```bash
make up-loadtest
```

If you want worker and outbox paths included:

```bash
make up-loadtest-worker
```

## Compose-Based Runner

The repository also includes [docker-compose.loadtest.yml](/Users/pluto/Documents/git/fastapi101/docker-compose.loadtest.yml), which defines a `k6` runner container.

Useful commands:

```bash
make up-loadtest
make loadtest-smoke
make loadtest-read
make loadtest-auth
make loadtest-soak
make down-loadtest
```

For worker and outbox scenarios:

```bash
make up-loadtest-worker
make loadtest-write
make down-loadtest-worker
```

This flow is useful when:

- the team does not want to install `k6` locally
- the same test runner should be used across machines
- monitoring should be available alongside the load test

## One-Command Orchestration

If you want to run the scenarios in sequence without typing each command, use [scripts/loadtest.sh](/Users/pluto/Documents/git/fastapi101/scripts/loadtest.sh).

Examples:

```bash
./scripts/loadtest.sh core
./scripts/loadtest.sh worker
./scripts/loadtest.sh full
```

Mode behavior:

- `core`
  Runs `smoke -> read -> auth`
- `worker`
  Runs `smoke -> read -> auth -> write`
- `full`
  Runs `smoke -> read -> auth -> write -> soak`

There is also a convenience Make target:

```bash
make loadtest-all
```

Recommended usage:

- use `core` for first-pass API validation
- use `worker` when testing async behavior without committing to a long soak
- use `full` when you want the closest thing to a full staged load test from one command

## Scenario Matrix

| Scenario | What It Proves | Main Endpoints | What To Watch |
| --- | --- | --- | --- |
| `smoke` | app is reachable and core endpoints respond before heavier tests start | `/health/live`, `/health/ready`, `/metrics` | immediate startup errors, readiness failures, missing metrics |
| `read baseline` | normal authenticated reads stay fast under increasing concurrency | `/api/v1/auth/me`, `/api/v1/items/` | p95 latency, cache effect, DB read saturation |
| `auth burst` | login/refresh/logout hold up under concentrated auth traffic | `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/logout` | auth latency, 401/429 behavior, rate-limit impact |
| `write + async` | writes and async side effects stay stable as user creation increases | `/api/v1/users/`, `/api/v1/items/` | write latency, DB pressure, outbox growth, queue depth |
| `soak` | system stays stable over time instead of only surviving short bursts | mixed auth/read traffic | memory growth, connection leaks, queue drift, readiness degradation |

## Starting SLO Targets

Use these as initial targets, then tune them to your product:

- read-heavy endpoints: `p95 < 300ms`
- auth endpoints: `p95 < 500ms`
- HTTP error rate: `< 1%`
- readiness: should not flap during nominal load
- DLQ depth: should remain `0` during normal load tests
- retry queue depth: may spike briefly, but should drain after the burst

These are not universal truth. They are good starting thresholds for a production-oriented internal API.

## Success Criteria By Scenario

### Smoke

Success means:

- `/health/live` is healthy
- `/health/ready` is healthy or clearly explains why it is degraded
- `/metrics` is scrapeable
- if metrics auth is enabled, the load-test environment or Prometheus config has the correct bearer token

### Read Baseline

Success means:

- p95 for `auth.me` and `items.list` stays within target
- error rate remains below threshold
- DB and cache metrics stay inside normal operating range

### Auth Burst

Success means:

- login and refresh endpoints stay under target latency
- expected auth failures are visible as controlled `401` or `429`, not `500`
- rate limiting protects the service without destabilizing it

### Write Plus Async

Success means:

- create-user traffic remains stable
- outbox rows are dispatched without indefinite growth
- queue depth rises and drains instead of growing forever
- worker failures stay near zero under normal test conditions

### Soak

Success means:

- latency does not drift steadily upward over time
- memory and DB connections do not leak
- readiness remains stable
- retries and queue backlog do not accumulate silently

## Metrics To Watch During Tests

Watch these at minimum:

- HTTP request rate
- p50, p95, and p99 latency
- `5xx` rate
- in-flight requests
- readiness failures
- DB CPU and connection usage
- cache hit/miss and Redis health
- auth event failures
- queue depth for main, retry, and dead-letter queues
- outbox dispatch success/failure

This starter already exposes many of these through the metrics stack included in the repo.

## Grafana And Query Cheat Sheet

If you bring up monitoring with `make up-loadtest` or `make up-loadtest-worker`, open:

- Grafana: `http://localhost:3001`
- Prometheus: `http://localhost:9090`

### Panels To Watch First

Use the built-in Grafana dashboard and start with these panels:

- `Request Rate`
  Confirms traffic is actually reaching the app at the level you expect.
- `5xx Rate`
  Shows whether the app is failing under stress instead of just slowing down.
- `P95 Latency`
  Best first signal for when the service starts missing its target.
- `In-Flight Requests`
  Helps reveal saturation or blocked work.
- `Auth Events`
  Useful during `auth burst` to distinguish expected auth failures from system instability.
- `Readiness Dependency Status`
  Shows whether database or optional dependencies degrade during the run.

### PromQL Queries For Load Tests

These are useful in Grafana Explore or Prometheus during a run.

- Request rate:

```promql
sum(rate(fastapi_template_http_requests_total[1m]))
```

- 5xx rate:

```promql
sum(rate(fastapi_template_http_requests_total{status_code=~"5.."}[5m]))
```

- P95 latency:

```promql
histogram_quantile(
  0.95,
  sum by (le) (rate(fastapi_template_http_request_duration_seconds_bucket[5m]))
)
```

- In-flight requests:

```promql
sum(fastapi_template_http_requests_in_progress)
```

- Auth event outcomes:

```promql
sum by (event, outcome) (rate(fastapi_template_auth_events_total[5m]))
```

- Readiness failures by dependency:

```promql
sum by (dependency, status) (rate(fastapi_template_readiness_checks_total[5m]))
```

- Latest readiness status:

```promql
max by (dependency) (fastapi_template_readiness_dependency_status)
```

- Cache hit/miss:

```promql
sum by (cache_name, outcome) (
  rate(fastapi_template_cache_operations_total{operation="get"}[5m])
)
```

- Worker outcomes:

```promql
sum by (task_name, outcome) (rate(fastapi_template_worker_events_total[5m]))
```

- Queue depth:

```promql
max by (queue_name) (fastapi_template_worker_queue_depth)
```

- Outbox dispatch outcomes:

```promql
sum by (outcome) (rate(fastapi_template_outbox_dispatch_events_total[5m]))
```

### Which Queries Matter For Which Scenario

- `read baseline`
  Focus on request rate, p95 latency, in-flight requests, cache hit/miss, and DB metrics.
- `auth burst`
  Focus on request rate, p95 latency, auth events, 401/429 mix, and 5xx rate.
- `write + async`
  Focus on request latency, worker outcomes, queue depth, and outbox dispatch outcomes.
- `soak`
  Focus on p95 latency over time, in-flight stability, readiness checks, queue depth drift, and any steady growth in failure counters.

## Interpreting Results

If the service slows down under read load first:

- inspect DB query plans
- verify indexes
- measure cache hit rate

If auth bursts fail first:

- inspect password-hash cost
- review rate-limit configuration
- check token/revocation persistence overhead

If write + async fails first:

- inspect DB write contention
- inspect outbox dispatch lag
- inspect worker throughput and retry behavior

If soak fails first:

- look for memory leaks
- look for DB connection leaks
- look for queues that slowly drift upward

## Operational Notes

Keep these test modes separate when possible:

- inline-only API testing
- worker-enabled testing
- worker + real provider integrations

For the first load-test pass, prefer:

- dry-run providers
- metrics enabled
- monitoring stack enabled
- worker enabled only when the test explicitly covers async behavior

That keeps the first round focused on the service itself before external providers distort the results.

## Before And After Each Run

Before:

- make sure the target stack is healthy
- confirm whether the `items` module is enabled
- decide whether providers should stay in dry-run mode
- open Grafana and Prometheus before traffic starts

After:

- export or screenshot key Grafana panels
- note p95 latency, error rate, readiness behavior, queue depth, and outbox behavior
- record the highest stable stage that stayed within your target
- tear the stack down with `make down-loadtest` or `make down-loadtest-worker`
