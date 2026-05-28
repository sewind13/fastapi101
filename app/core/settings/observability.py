import json

from pydantic import BaseModel, Field, field_validator


class LoggingSettings(BaseModel):
    level: str = "INFO"
    audit_level: str = "INFO"
    schema_version: str = "1.0"
    access_log_sample_rate: float = 1.0
    access_log_skip_paths: list[str] = Field(default_factory=lambda: ["/health/live"])
    access_log_skip_prefixes: list[str] = Field(default_factory=list)
    trace_header_name: str = "traceparent"

    @field_validator("access_log_skip_paths", "access_log_skip_prefixes", mode="before")
    @classmethod
    def parse_skip_paths(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]

        return value

    @field_validator("access_log_sample_rate")
    @classmethod
    def validate_sample_rate(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class TelemetrySettings(BaseModel):
    enabled: bool = False
    service_name: str = "fastapi-template"
    service_version: str = "0.1.0"
    exporter_otlp_endpoint: str | None = None
    exporter_otlp_insecure: bool = True


class HealthSettings(BaseModel):
    timeout_seconds: float = 2.0
    enable_redis_check: bool = False
    redis_url: str | None = None
    enable_s3_check: bool = False
    s3_endpoint_url: str | None = None
    s3_bucket_name: str | None = None
    s3_region: str | None = None
    enable_queue_check: bool = False
    queue_url: str | None = None


class MetricsSettings(BaseModel):
    enabled: bool = False
    path: str = "/metrics"
    include_in_schema: bool = False
    auth_token: str | None = None


class CacheSettings(BaseModel):
    enabled: bool = False
    backend: str = "memory"
    redis_url: str | None = None
    key_prefix: str = "cache"
    default_ttl_seconds: int = 60
    items_list_ttl_seconds: int = 30

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("CACHE__BACKEND must be either 'memory' or 'redis'.")
        return normalized
