import re
from uuid import uuid4

from fastapi import Request

from app.core.config import settings

REQUEST_ID_HEADER = "X-Request-ID"
TRACEPARENT_PATTERN = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace_id>[0-9a-f]{32})-(?P<span_id>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid4())


def get_trace_context(request: Request) -> tuple[str | None, str | None]:
    try:
        from opentelemetry.trace import get_current_span

        span = get_current_span()
        span_context = span.get_span_context()
        if span_context and span_context.is_valid:
            return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"
    except Exception:
        pass

    traceparent = request.headers.get(settings.logging.trace_header_name)
    if not traceparent:
        return None, None

    match = TRACEPARENT_PATTERN.match(traceparent.strip())
    if not match:
        return None, None

    return match.group("trace_id"), match.group("span_id")
