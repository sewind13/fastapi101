# Deployment Guide

This guide explains how the template is intended to run outside local development.

## Production-Like Docker Flow

Use the base compose file to run the app without source-code bind mounts:

```bash
make up-prod
make down-prod
make ps-prod
make logs-prod
```

This mode:

- uses the image exactly as built
- does not mount local source into the container
- uses dependencies baked into the image
- avoids installing packages during container startup
- is closer to a real deployment runtime shape
- keeps compose-exposed ports bound to `127.0.0.1` by default for safer local use
- uses `LOCAL_POSTGRES_*` and `LOCAL_RABBITMQ_*` variables so local credentials are clearly separated from real deployment secrets

The container starts through [`scripts/start-web.sh`](../scripts/start-web.sh):

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If you enable the background worker, run it as a separate process from the same image:

```bash
python -m app.worker.runner
```

If you enable the transactional outbox flow, also run the outbox dispatcher:

```bash
python -m app.jobs.dispatch_outbox
```

Recommended production pattern:

- run the API and worker as separate deployable processes
- run the outbox dispatcher as a separate process
- point both at the same broker and config source
- scale the worker independently from the API
- configure retry and dead-letter queues so failed tasks do not spin in hot loops
- use Redis-backed worker idempotency for multi-instance worker deployments
- lock down operations endpoints with strong auth and an explicit role-based authorization model such as `ops_admin` or `platform_admin`
- do not treat compose port bindings or demo credentials as production-safe defaults
- do not copy `LOCAL_POSTGRES_*` or `LOCAL_RABBITMQ_*` values into production manifests

Example production-oriented env baseline:

- [/.env.prod.example](/Users/pluto/Documents/git/fastapi101/.env.prod.example)

The main CI workflow now also carries baseline deployment validation:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- runs `actionlint` against workflow files
- runs `helm lint`, `helm template`, and `kubeconform` against the bundled Helm chart
- gates the main Python quality job on those checks first

## Recommended End-To-End Production Shape

For a real production deployment, treat this template as several cooperating runtime units instead of one giant container:

- API deployment
- worker deployment
- outbox-dispatcher deployment
- migration job or release step
- managed or external Postgres
- managed or external Redis when distributed cache, rate limiting, or idempotency is enabled
- managed or external broker when worker features are enabled
- reverse proxy, ingress, or load balancer in front of the API
- metrics and log collection pipeline

Recommended baseline:

- run the API as stateless replicas
- run workers separately from the API
- run the outbox dispatcher separately from both
- run migrations before new API traffic is admitted
- keep Postgres and Redis outside the app deployment boundary in production-like environments

## End-To-End Deployment Sequence

Use this sequence as the default release flow:

1. Build one immutable application image.
2. Run quality checks in CI:
   - lint
   - typecheck
   - unit tests
   - integration tests
3. Publish the image to your registry.
4. Render or apply environment-specific config and secrets.
5. Run Alembic migrations from the same image that will run the app.
6. Deploy or roll the API workload.
7. Wait for `/health/ready` to pass on new API instances.
8. Deploy or roll the worker workload if enabled.
9. Deploy or roll the outbox dispatcher if enabled.
10. Verify key smoke checks:
    - login
    - one protected API route
    - `/health/ready`
    - metrics scrape
    - worker publishing and consumption if enabled

This order matters:

- migrations happen before traffic cutover
- API readiness gates traffic admission
- background processes are rolled after the schema they depend on is in place

## Runtime Responsibilities

### API

The API should be responsible for:

- serving synchronous HTTP requests
- performing request-scoped DB work
- writing outbox rows when async side effects are enabled
- exposing health and metrics endpoints

The API should not be the place where long-running background work happens.

### Worker

The worker should be responsible for:

- consuming broker messages
- applying retry and dead-letter semantics
- enforcing worker idempotency
- handling external side effects such as email or webhook delivery

### Outbox Dispatcher

The dispatcher should be responsible for:

- polling committed outbox rows
- publishing those rows to the broker
- marking dispatch outcomes

Keep the dispatcher separate so request latency does not depend on broker publishing.

## Environment Sources

Split environment data into three groups:

- non-secret config
- secrets
- platform wiring

Examples:

- non-secret config:
  `APP__ENV`, `API__CORS_ORIGINS`, `METRICS__PATH`
- secrets:
  `SECURITY__SECRET_KEY`, credential-bearing URLs, provider API keys
- platform wiring:
  service DNS names, ingress rules, autoscaling settings, scrape jobs

Use:

- ConfigMaps or equivalent for non-secret config
- a secret manager or platform secret store for secrets
- deployment manifests or Helm values for platform wiring

The Kubernetes examples in this repository now follow that split more closely:

- non-secret values in [deploy/kubernetes/app-configmap.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-configmap.yaml)
- secret-bearing values in [deploy/kubernetes/app-secret.example.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/app-secret.example.yaml)
- a separate migration job example in [deploy/kubernetes/migration-job.yaml](/Users/pluto/Documents/git/fastapi101/deploy/kubernetes/migration-job.yaml)
- a Helm baseline in [deploy/helm/fastapi-template](/Users/pluto/Documents/git/fastapi101/deploy/helm/fastapi-template)

## Migration Strategy

Alembic is the schema source of truth.

Important files:

- [`alembic/env.py`](../alembic/env.py)
- [`alembic/versions/20260402_0001_initial_schema.py`](../alembic/versions/20260402_0001_initial_schema.py)
- [`app/db/base.py`](../app/db/base.py)

Normal workflow:

1. update SQLModel models
2. create a migration
3. apply migrations
4. run tests

Commands:

```bash
make migration m="add orders table"
make migrate
make psql
```

For real deployments, prefer one of these patterns:

- init job runs migrations before the app becomes ready
- release pipeline runs migrations before switching traffic
- a dedicated migration job runs from the same application image

Recommended production default:

- migration job or release step runs first
- API rollout happens only after migration success
- rollback never means "blindly downgrade the database" unless the migration was explicitly written to support it

## Health Endpoints

Available endpoints:

- `/health`: generic app health
- `/health/live`: liveness probe
- `/health/ready`: readiness probe with dependency detail

Readiness checks:

- database connectivity
- Redis `PING` when enabled
- S3 `head_bucket` when enabled
- queue/broker connection when enabled

Use them like this:

- use `/health/live` for restart decisions
- use `/health/ready` for traffic admission
- do not use `/health` as a substitute for readiness

Recommended production wiring:

- load balancer or ingress uses `/health/ready`
- process supervisor or container runtime uses `/health/live`
- dashboards and probes record both

## Reverse Proxy And Ingress

In real deployments, the application is often not exposed directly to the public internet. A reverse proxy, ingress controller, or load balancer usually sits in front of the app.

That layer is typically responsible for:

- TLS termination
- public routing
- edge rate limiting or WAF rules
- forwarding client IP metadata

### Nginx Reverse Proxy Example

Example Nginx location block:

```nginx
location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://app:8000;
}
```

If you want the application to trust forwarded client IPs for auth rate limiting:

- set `AUTH_RATE_LIMIT__TRUST_PROXY_HEADERS=true`
- set `AUTH_RATE_LIMIT__TRUSTED_PROXY_CIDRS` to the IP ranges of your reverse-proxy tier
- verify that the direct peer IP seen by the app belongs to that trusted tier

Do not trust forwarded IP headers from arbitrary clients.

### Kubernetes Ingress Guidance

Typical split of responsibilities:

- ingress/load balancer handles public traffic and TLS
- app service only receives internal cluster traffic
- app readiness is used for traffic admission
- app liveness is used for restart decisions

Recommended probe usage:

- use `/health/live` for liveness probes
- use `/health/ready` for readiness probes
- do not point both probes at the same path unless you intentionally want identical behavior

Example probe shape:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
```

If you use ingress, also verify:

- the app can identify trusted proxy peers correctly
- ingress timeouts are longer than your normal API latency budget
- client IP forwarding still works after ingress or load balancer changes
- `/metrics` is not publicly routed unless explicitly intended

## Prometheus Metrics

The template can expose Prometheus metrics at:

- `METRICS__PATH`
- default: `/metrics`
- `METRICS__AUTH_TOKEN`
- when configured, clients must send `Authorization: Bearer <token>`

Current baseline metrics include:

- total HTTP requests by method, path, and status code
- HTTP request duration histogram
- in-flight HTTP requests
- application exception totals by exception type, error code, path, and status
- readiness check totals by dependency and status
- latest readiness dependency status gauge
- auth business events such as login, refresh, and logout outcomes
- maintenance job runs and deleted-row totals
- background worker task events by task name and outcome
- background worker queue depth gauges for main, retry, and dead-letter queues
- outbox dispatch event totals by outcome

The request-duration histogram uses buckets tuned for typical API traffic:

- `5ms`, `10ms`, `25ms`, `50ms`
- `100ms`, `250ms`, `500ms`
- `1s`, `2.5s`, `5s`, `10s`

This gives decent visibility across:

- very fast in-memory/cache-heavy endpoints
- normal DB-backed CRUD endpoints
- slower dependency-heavy or degraded requests

Recommended production pattern:

- let Prometheus scrape the app on the internal network
- keep `/metrics` off the public internet unless intentionally exposed
- pair metrics with alerts for error rate, latency, and saturation
- if app-level metrics auth is enabled, configure the same bearer token in Prometheus

For ingress-based deployments:

- prefer scraping the app service internally instead of routing Prometheus through the public ingress
- if you must expose `/metrics`, protect it with network policy, auth, or private ingress rules

## Production Rate Limiting

For real multi-instance deployment, set:

- `AUTH_RATE_LIMIT__BACKEND="redis"`
- `AUTH_RATE_LIMIT__REDIS_URL=...`

Use `memory` only for local development or simple single-instance environments.

Suggested alerting starting points:

- `5xx rate`: alert if `5xx` responses exceed `1%` of traffic for 5 minutes
- `p95 latency`: alert if p95 exceeds `500ms` for 10 minutes on core endpoints
- `in-flight requests`: alert if in-flight stays above a normal steady-state threshold for 5-10 minutes
- `readiness failures`: alert immediately if `database` readiness is failed, or if any critical dependency stays failed for more than 2-5 minutes

Tune these thresholds to your product profile:

- low-latency internal APIs may want tighter latency thresholds
- bursty public APIs may need higher in-flight thresholds
- non-critical dependencies can page later than database failures

## Monitoring Examples

This repo also includes monitoring examples:

- [`deploy/monitoring/prometheus.yml`](../deploy/monitoring/prometheus.yml)
- [`deploy/monitoring/prometheus-alerts.yml`](../deploy/monitoring/prometheus-alerts.yml)
- [`deploy/monitoring/alertmanager.yml`](../deploy/monitoring/alertmanager.yml)
- [`deploy/monitoring/grafana-dashboard-fastapi-template.json`](../deploy/monitoring/grafana-dashboard-fastapi-template.json)
- [`deploy/monitoring/grafana/provisioning/datasources/prometheus.yml`](../deploy/monitoring/grafana/provisioning/datasources/prometheus.yml)
- [`deploy/monitoring/grafana/provisioning/dashboards/dashboard-provider.yml`](../deploy/monitoring/grafana/provisioning/dashboards/dashboard-provider.yml)
- [`docker-compose.monitoring.yml`](../docker-compose.monitoring.yml)

Example local workflow:

```bash
make up-monitoring
```

Then open:

- Prometheus: `http://localhost:9090`
- all monitoring ports are bound to `127.0.0.1` by default in compose for local-only access
- Grafana: `http://localhost:3001`
- Alertmanager: `http://localhost:9093`

Grafana provisioning in this repo:

- auto-loads a Prometheus datasource
- auto-loads the FastAPI template dashboard
- uses demo credentials `admin` / `admin` for local-only monitoring

Alertmanager example in this repo:

- includes webhook receiver examples

## Release Rollback Principles

Application rollback and database rollback are not the same thing.

Recommended rule:

- roll back the application image first when a release fails
- only roll back the database schema when the migration was explicitly designed and rehearsed to be reversible

Safer default rollback path:

1. stop or pause traffic cutover
2. restore the previous API image
3. restore the previous worker and dispatcher images if needed
4. verify app behavior against the new schema
5. if the schema itself is the problem, use a prepared remediation migration or restore-from-backup plan instead of ad hoc downgrade attempts

## Related Production Docs

- [docs/production-topology.md](/Users/pluto/Documents/git/fastapi101/docs/production-topology.md)
- [docs/observability.md](/Users/pluto/Documents/git/fastapi101/docs/observability.md)
- [docs/first-deploy-checklist.md](/Users/pluto/Documents/git/fastapi101/docs/first-deploy-checklist.md)
- [docs/secret-management.md](/Users/pluto/Documents/git/fastapi101/docs/secret-management.md)
- includes Slack and email example receivers as placeholders
- should be edited before any real use

The Prometheus example also loads baseline alert rules for:

- high `5xx` rate
- high p95 latency
- high in-flight requests
- database readiness failure
- critical dependency readiness failure
- elevated login failures
- cleanup job failures
- worker failures and dead-letter activity
- retry-queue backlog
- duplicate-skipped worker events when idempotency prevents re-processing

When operating worker queues:

- dead-letter queues should normally stay empty
- replay DLQ traffic only after fixing the underlying task failure
- avoid blind replay loops during active incidents

Before real use, replace placeholder values in:

- [`deploy/monitoring/alertmanager.yml`](../deploy/monitoring/alertmanager.yml)

## Deployment Notes

- keep real secrets out of `.env` in shared repos
- prefer nested env vars such as `APP__NAME` and `DATABASE__URL`
- use your platform secret manager in real production
- treat `docker-compose.yml` as a production-like local artifact, not as a full production manifest

For a fuller secret-handling and rotation playbook, see [docs/secret-management.md](/Users/pluto/Documents/git/fastapi101/docs/secret-management.md).

## Kubernetes And Nginx Examples

This repo includes deployment examples you can adapt:

- [`deploy/kubernetes/app-configmap.yaml`](../deploy/kubernetes/app-configmap.yaml)
- [`deploy/kubernetes/app-deployment.yaml`](../deploy/kubernetes/app-deployment.yaml)
- [`deploy/kubernetes/app-hpa.yaml`](../deploy/kubernetes/app-hpa.yaml)
- [`deploy/kubernetes/app-ingress.yaml`](../deploy/kubernetes/app-ingress.yaml)
- [`deploy/kubernetes/app-networkpolicy.yaml`](../deploy/kubernetes/app-networkpolicy.yaml)
- [`deploy/kubernetes/app-secret.example.yaml`](../deploy/kubernetes/app-secret.example.yaml)
- [`deploy/kubernetes/kustomization.yaml`](../deploy/kubernetes/kustomization.yaml)
- [`deploy/kubernetes/worker-deployment.yaml`](../deploy/kubernetes/worker-deployment.yaml)
- [`deploy/kubernetes/outbox-dispatcher-deployment.yaml`](../deploy/kubernetes/outbox-dispatcher-deployment.yaml)
- [`deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml`](../deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml)
- [`deploy/kubernetes/migration-job.yaml`](../deploy/kubernetes/migration-job.yaml)
- [`deploy/helm/fastapi-template`](../deploy/helm/fastapi-template)
- [`deploy/nginx/nginx.conf`](../deploy/nginx/nginx.conf)

These files are intentionally baseline examples:

- replace image names
- replace hostnames
- connect them to your real Secret / ConfigMap names
- tune replica count and resource requests for your environment
- review ingress annotations and timeouts against your platform

For production:

- prefer running migrations as a separate init or release step
- keep `/metrics` internal unless intentionally exposed
- combine ingress limits with application-level rate limiting
- verify trusted proxy CIDRs before enabling forwarded-header trust
- run worker replicas separately from API replicas when background throughput matters

Suggested Kubernetes workflow:

1. copy the secret example into your secret-management flow or replace the `secretGenerator`
2. update the ConfigMap values for your environment
3. replace image names and tags
4. tune replicas, requests, and limits
5. adjust ingress hostnames, TLS secret name, and annotations
6. review network policy ports and namespace selectors
7. tune HPA min/max replicas and target utilization
8. apply with `kubectl apply -k deploy/kubernetes`
9. run the migration job separately when you want Kubernetes to own schema rollout:
   `kubectl apply -f deploy/kubernetes/migration-job.yaml`

Suggested Helm workflow:

1. copy `deploy/helm/fastapi-template/values.yaml`
2. use `deploy/helm/fastapi-template/values.prod.example.yaml` as a production-oriented starting point when you want a fuller baseline
3. replace image, hostnames, and all secret placeholders
4. decide whether Helm should create the migration job or whether your release system runs migrations separately
5. disable worker or dispatcher templates if the service does not use them
6. render and review with `helm template`
7. install or upgrade with your normal Helm release workflow

Example GitHub Actions release workflow:

- [`.github/workflows/release-example.yml`](../.github/workflows/release-example.yml)
- [`.github/workflows/helm-validate-example.yml`](../.github/workflows/helm-validate-example.yml)
- [`.github/workflows/release-eks-oidc-example.yml`](../.github/workflows/release-eks-oidc-example.yml)
- [`.github/workflows/release-gke-oidc-example.yml`](../.github/workflows/release-gke-oidc-example.yml)
- [`.github/workflows/release-aks-oidc-example.yml`](../.github/workflows/release-aks-oidc-example.yml)
- [`.github/workflows/workflow-validate-example.yml`](../.github/workflows/workflow-validate-example.yml)

That example now assumes a repository secret named `KUBE_CONFIG` and:

- builds and pushes the image
- renders and runs the Helm migration job with the same image tag
- deploys the main release with `migrationJob.enabled=false`
- waits for rollout on API, worker, and dispatcher workloads

You should still adapt it to your real authentication model and namespace conventions before using it as a real release pipeline.

If you want a provider-specific example, the EKS OIDC workflow assumes repository variables:

- `AWS_REGION`
- `EKS_CLUSTER_NAME`
- `AWS_ROLE_ARN`

and uses GitHub OIDC plus `aws eks update-kubeconfig` instead of a raw kubeconfig secret.

The EKS workflow is the most production-oriented starting point in this repo right now. It also includes:

- a preflight check for required repository variables
- serialized release concurrency per Helm release and namespace
- migration logs after the migration job succeeds
- optional worker and outbox-dispatcher rollout waits
- a short deployed-workload summary after Helm upgrade completes

The GKE OIDC workflow assumes repository variables:

- `GCP_PROJECT_ID`
- `GKE_CLUSTER_NAME`
- `GKE_CLUSTER_LOCATION`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

and uses `google-github-actions/auth` plus `get-gke-credentials`.

The AKS OIDC workflow assumes repository variables:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AKS_RESOURCE_GROUP`
- `AKS_CLUSTER_NAME`

and uses `azure/login` plus `azure/aks-set-context`.

If you only want to validate workflow files themselves, the actionlint example gives a small starting point for CI:

- `actionlint` checks GitHub Actions workflow structure and many common mistakes
- keep it separate from the main release workflow so you can adopt it without changing deploy behavior

For Helm and manifest validation, the Helm validation workflow now demonstrates:

- `helm lint`
- `helm template` with default values
- `helm template` with production example values
- `kubeconform` schema validation against the rendered manifests

NetworkPolicy note:

- the example is intentionally broad enough to be a starter
- tighten namespace selectors and egress destinations for your cluster
- verify required ports for your real dependencies before enforcing it

HPA note:

- the example assumes the cluster has metrics-server or an equivalent metrics pipeline
- CPU and memory targets are placeholders and should be tuned from real traffic data

## Related Files

- [`Dockerfile`](../Dockerfile)
- [`docker-compose.yml`](../docker-compose.yml)
- [`docker-compose.dev.yml`](../docker-compose.dev.yml)
- [`deploy/kubernetes/app-configmap.yaml`](../deploy/kubernetes/app-configmap.yaml)
- [`deploy/kubernetes/app-deployment.yaml`](../deploy/kubernetes/app-deployment.yaml)
- [`deploy/kubernetes/app-hpa.yaml`](../deploy/kubernetes/app-hpa.yaml)
- [`deploy/kubernetes/app-ingress.yaml`](../deploy/kubernetes/app-ingress.yaml)
- [`deploy/kubernetes/app-networkpolicy.yaml`](../deploy/kubernetes/app-networkpolicy.yaml)
- [`deploy/kubernetes/app-secret.example.yaml`](../deploy/kubernetes/app-secret.example.yaml)
- [`deploy/kubernetes/kustomization.yaml`](../deploy/kubernetes/kustomization.yaml)
- [`deploy/kubernetes/worker-deployment.yaml`](../deploy/kubernetes/worker-deployment.yaml)
- [`deploy/kubernetes/outbox-dispatcher-deployment.yaml`](../deploy/kubernetes/outbox-dispatcher-deployment.yaml)
- [`deploy/kubernetes/migration-job.yaml`](../deploy/kubernetes/migration-job.yaml)
- [`deploy/helm/fastapi-template`](../deploy/helm/fastapi-template)
- [`deploy/helm/fastapi-template/values.prod.example.yaml`](../deploy/helm/fastapi-template/values.prod.example.yaml)
- [`../.github/workflows/release-example.yml`](../.github/workflows/release-example.yml)
- [`../.github/workflows/helm-validate-example.yml`](../.github/workflows/helm-validate-example.yml)
- [`../.github/workflows/release-eks-oidc-example.yml`](../.github/workflows/release-eks-oidc-example.yml)
- [`../.github/workflows/release-gke-oidc-example.yml`](../.github/workflows/release-gke-oidc-example.yml)
- [`../.github/workflows/release-aks-oidc-example.yml`](../.github/workflows/release-aks-oidc-example.yml)
- [`../.github/workflows/workflow-validate-example.yml`](../.github/workflows/workflow-validate-example.yml)
- [`scripts/start-web.sh`](../scripts/start-web.sh)
- [`scripts/start-dev.sh`](../scripts/start-dev.sh)
- [`deploy/nginx/nginx.conf`](../deploy/nginx/nginx.conf)
- [`deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml`](../deploy/kubernetes/cleanup-revoked-tokens-cronjob.yaml)
