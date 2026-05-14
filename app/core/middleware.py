from random import random
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import logger, redact_data
from app.core.metrics import observe_request, track_in_progress
from app.core.request import REQUEST_ID_HEADER, get_request_id, get_trace_context


def request_log_extra(
    request: Request,
    *,
    status_code: int,
    error_code: str | None = None,
    duration_ms: float | None = None,
) -> dict:
    query_params = redact_data(dict(request.query_params))
    headers = redact_data(
        {
            "user-agent": request.headers.get("user-agent"),
            "authorization": request.headers.get("authorization"),
            "x-request-id": request.headers.get(REQUEST_ID_HEADER),
        }
    )
    client_ip = request.client.host if request.client else None
    trace_id, span_id = get_trace_context(request)

    extra = {
        "request_id": get_request_id(request),
        "path": request.url.path,
        "method": request.method,
        "status_code": status_code,
        "client_ip": client_ip,
        "query_params": query_params,
        "headers": headers,
        "request_size_bytes": int(request.headers.get("content-length", "0") or 0),
        "trace_id": trace_id,
        "span_id": span_id,
    }
    if error_code is not None:
        extra["error_code"] = error_code
    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)
    return extra


async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER) or get_request_id(request)
    request.state.request_id = request_id
    start_time = perf_counter()
    in_progress = track_in_progress(method=request.method, path=request.url.path)
    try:
        response = await call_next(request)
        duration_seconds = perf_counter() - start_time
        duration_ms = duration_seconds * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        observe_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        should_skip = request.url.path in settings.logging.access_log_skip_paths or any(
            request.url.path.startswith(prefix)
            for prefix in settings.logging.access_log_skip_prefixes
        )
        should_sample = random() <= settings.logging.access_log_sample_rate
        if response.status_code >= 400 or (not should_skip and should_sample):
            extra = request_log_extra(
                request,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            extra["response_size_bytes"] = int(response.headers.get("content-length", "0") or 0)
            logger.info("request completed", extra=extra)
        return response
    finally:
        in_progress.dec()


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_context_middleware)
