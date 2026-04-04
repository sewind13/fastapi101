import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "secret_key",
    "api_key",
}

REDACTED = "***REDACTED***"


def redact_value(key: str, value: Any) -> Any:
    normalized_key = key.lower()
    if normalized_key in SENSITIVE_KEYS:
        return REDACTED

    if isinstance(value, dict):
        return redact_data(value)

    if isinstance(value, list):
        return [redact_value(key, item) for item in value]

    return value


def redact_data(data: dict[str, Any]) -> dict[str, Any]:
    return {key: redact_value(key, value) for key, value in data.items()}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "schema_version": settings.logging.schema_version,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in (
            "request_id",
            "path",
            "method",
            "status_code",
            "error_code",
            "duration_ms",
            "client_ip",
            "query_params",
            "headers",
            "request_size_bytes",
            "response_size_bytes",
            "event_type",
            "deleted_count",
            "task_name",
            "queue_name",
            "retry_count",
            "published_count",
            "retried_count",
            "failed_count",
            "username",
            "user_id",
            "token_type",
            "trace_id",
            "span_id",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.logging.level.upper())


logger = logging.getLogger("app")
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(settings.logging.audit_level.upper())


def log_audit_event(event: str, **fields: Any) -> None:
    audit_logger.info(event, extra=redact_data(fields))
