from dataclasses import dataclass

from app.core.config import settings
from app.core.metrics import observe_readiness_check
from app.db.session import check_db_connection
from app.schemas.common import DependencyCheckResponse, ReadinessResponse


@dataclass(slots=True)
class CheckResult:
    name: str
    status: str
    message: str | None = None


def _redis_check() -> CheckResult:
    if not settings.health.redis_url:
        return CheckResult(name="redis", status="failed", message="Redis URL is not configured.")

    try:
        from redis import Redis
    except ImportError:
        return CheckResult(
            name="redis",
            status="failed",
            message="Redis client dependency is not installed.",
        )

    client = Redis.from_url(
        settings.health.redis_url,
        socket_timeout=settings.health.timeout_seconds,
        socket_connect_timeout=settings.health.timeout_seconds,
    )
    try:
        client.ping()
        return CheckResult(name="redis", status="ok")
    except Exception as exc:
        return CheckResult(name="redis", status="failed", message=str(exc))
    finally:
        client.close()


def _s3_check() -> CheckResult:
    if not settings.health.s3_endpoint_url:
        return CheckResult(name="s3", status="failed", message="S3 endpoint URL is not configured.")

    if not settings.health.s3_bucket_name:
        return CheckResult(name="s3", status="failed", message="S3 bucket name is not configured.")

    try:
        import boto3  # type: ignore[import-untyped]
        from botocore.config import Config  # type: ignore[import-untyped]
    except ImportError:
        return CheckResult(
            name="s3",
            status="failed",
            message="S3 client dependency is not installed.",
        )

    client = boto3.client(
        "s3",
        endpoint_url=settings.health.s3_endpoint_url,
        region_name=settings.health.s3_region,
        config=Config(
            connect_timeout=settings.health.timeout_seconds,
            read_timeout=settings.health.timeout_seconds,
        ),
    )
    try:
        client.head_bucket(Bucket=settings.health.s3_bucket_name)
        return CheckResult(name="s3", status="ok")
    except Exception as exc:
        return CheckResult(name="s3", status="failed", message=str(exc))
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def _queue_check() -> CheckResult:
    if not settings.health.queue_url:
        return CheckResult(name="queue", status="failed", message="Queue URL is not configured.")

    try:
        import pika  # type: ignore[import-untyped]
    except ImportError:
        return CheckResult(
            name="queue",
            status="failed",
            message="AMQP client dependency is not installed.",
        )

    parameters = pika.URLParameters(settings.health.queue_url)
    parameters.socket_timeout = settings.health.timeout_seconds
    parameters.stack_timeout = settings.health.timeout_seconds
    parameters.blocked_connection_timeout = settings.health.timeout_seconds

    connection = None
    try:
        connection = pika.BlockingConnection(parameters)
        return CheckResult(name="queue", status="ok")
    except Exception as exc:
        return CheckResult(name="queue", status="failed", message=str(exc))
    finally:
        if connection is not None and connection.is_open:
            connection.close()


def run_readiness_checks() -> ReadinessResponse:
    checks: list[CheckResult] = []

    try:
        check_db_connection()
        checks.append(CheckResult(name="database", status="ok"))
    except Exception as exc:
        checks.append(CheckResult(name="database", status="failed", message=str(exc)))

    if settings.health.enable_redis_check:
        checks.append(_redis_check())
    else:
        checks.append(CheckResult(name="redis", status="skipped", message="Check disabled."))

    if settings.health.enable_s3_check:
        checks.append(_s3_check())
    else:
        checks.append(CheckResult(name="s3", status="skipped", message="Check disabled."))

    if settings.health.enable_queue_check:
        checks.append(_queue_check())
    else:
        checks.append(CheckResult(name="queue", status="skipped", message="Check disabled."))

    for check in checks:
        observe_readiness_check(dependency=check.name, status=check.status)

    overall_status = "ok" if all(check.status != "failed" for check in checks) else "degraded"

    return ReadinessResponse(
        status=overall_status,
        checks=[
            DependencyCheckResponse(
                name=check.name,
                status=check.status,
                message=check.message,
            )
            for check in checks
        ],
    )
