from pydantic import BaseModel, field_validator


class WorkerSettings(BaseModel):
    enabled: bool = False
    broker_url: str | None = None
    queue_name: str = "app.default"
    retry_queue_name: str = "app.default.retry"
    dead_letter_queue_name: str = "app.default.dlq"
    prefetch_count: int = 10
    max_retries: int = 3
    retry_delay_ms: int = 30000
    max_retry_delay_ms: int = 300000
    requeue_on_failure: bool = False
    idempotency_enabled: bool = True
    idempotency_backend: str = "memory"
    idempotency_redis_url: str | None = None
    idempotency_key_prefix: str = "worker_idempotency"
    idempotency_ttl_seconds: int = 86400

    @field_validator("idempotency_backend")
    @classmethod
    def validate_idempotency_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("WORKER__IDEMPOTENCY_BACKEND must be either 'memory' or 'redis'.")
        return normalized
