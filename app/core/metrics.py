from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

METRICS_NAMESPACE = "fastapi_template"

registry = CollectorRegistry()

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed.",
    labelnames=("method", "path", "status_code"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "path"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed.",
    labelnames=("method", "path"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

app_exceptions_total = Counter(
    "app_exceptions_total",
    "Total number of application exceptions observed.",
    labelnames=("exception_type", "error_code", "path", "status_code"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

readiness_checks_total = Counter(
    "readiness_checks_total",
    "Total number of readiness dependency checks by dependency and status.",
    labelnames=("dependency", "status"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

readiness_dependency_status = Gauge(
    "readiness_dependency_status",
    "Latest readiness dependency status. 1=ok, 0=skipped, -1=failed.",
    labelnames=("dependency",),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

auth_events_total = Counter(
    "auth_events_total",
    "Total number of auth business events.",
    labelnames=("event", "outcome"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

maintenance_job_runs_total = Counter(
    "maintenance_job_runs_total",
    "Total number of maintenance job runs by job name and outcome.",
    labelnames=("job_name", "outcome"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

maintenance_job_deleted_total = Counter(
    "maintenance_job_deleted_total",
    "Total number of deleted records produced by maintenance jobs.",
    labelnames=("job_name",),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

worker_events_total = Counter(
    "worker_events_total",
    "Total number of background worker task events.",
    labelnames=("task_name", "outcome"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

worker_queue_depth = Gauge(
    "worker_queue_depth",
    "Latest observed worker queue depth by queue name.",
    labelnames=("queue_name",),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

outbox_dispatch_events_total = Counter(
    "outbox_dispatch_events_total",
    "Total number of outbox dispatch outcomes.",
    labelnames=("outcome",),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)

cache_operations_total = Counter(
    "cache_operations_total",
    "Total number of cache operations by cache name, backend, operation, and outcome.",
    labelnames=("cache_name", "backend", "operation", "outcome"),
    namespace=METRICS_NAMESPACE,
    registry=registry,
)


def observe_request(*, method: str, path: str, status_code: int, duration_seconds: float) -> None:
    http_requests_total.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration_seconds)


def observe_exception(
    *,
    exception_type: str,
    error_code: str,
    path: str,
    status_code: int,
) -> None:
    app_exceptions_total.labels(
        exception_type=exception_type,
        error_code=error_code,
        path=path,
        status_code=str(status_code),
    ).inc()


def observe_readiness_check(*, dependency: str, status: str) -> None:
    readiness_checks_total.labels(dependency=dependency, status=status).inc()
    readiness_dependency_status.labels(dependency=dependency).set(
        {
            "ok": 1,
            "skipped": 0,
            "failed": -1,
        }.get(status, -1)
    )


def observe_auth_event(*, event: str, outcome: str) -> None:
    auth_events_total.labels(event=event, outcome=outcome).inc()


def observe_maintenance_run(*, job_name: str, outcome: str, deleted_count: int = 0) -> None:
    maintenance_job_runs_total.labels(job_name=job_name, outcome=outcome).inc()
    if deleted_count > 0:
        maintenance_job_deleted_total.labels(job_name=job_name).inc(deleted_count)


def observe_worker_event(*, task_name: str, outcome: str) -> None:
    worker_events_total.labels(task_name=task_name, outcome=outcome).inc()


def observe_worker_queue_depth(*, queue_name: str, depth: int) -> None:
    worker_queue_depth.labels(queue_name=queue_name).set(depth)


def observe_outbox_dispatch(*, outcome: str, count: int = 1) -> None:
    if count > 0:
        outbox_dispatch_events_total.labels(outcome=outcome).inc(count)


def observe_cache_operation(
    *,
    cache_name: str,
    backend: str,
    operation: str,
    outcome: str,
) -> None:
    cache_operations_total.labels(
        cache_name=cache_name,
        backend=backend,
        operation=operation,
        outcome=outcome,
    ).inc()


def track_in_progress(*, method: str, path: str):
    gauge = http_requests_in_progress.labels(method=method, path=path)
    gauge.inc()
    return gauge


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST
