from random import random
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, UnauthorizedException
from app.core.health import run_readiness_checks
from app.core.logging import configure_logging, logger, redact_data
from app.core.metrics import (
    observe_exception,
    observe_request,
    render_metrics,
    track_in_progress,
)
from app.core.request import REQUEST_ID_HEADER, get_request_id, get_trace_context
from app.core.telemetry import configure_telemetry
from app.db.session import engine
from app.schemas.common import ErrorResponse, HealthResponse, ReadinessResponse

configure_logging()

app = FastAPI(
    title=settings.app.name,
    openapi_url=f"{settings.api.v1_prefix}/openapi.json",
)
configure_telemetry(app, engine=engine)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _request_log_extra(
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


@app.middleware("http")
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
        should_skip = (
            request.url.path in settings.logging.access_log_skip_paths
            or any(
                request.url.path.startswith(prefix)
                for prefix in settings.logging.access_log_skip_prefixes
            )
        )
        should_sample = random() <= settings.logging.access_log_sample_rate
        if response.status_code >= 400 or (not should_skip and should_sample):
            extra = _request_log_extra(
                request,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            extra["response_size_bytes"] = int(response.headers.get("content-length", "0") or 0)
            logger.info("request completed", extra=extra)
        return response
    finally:
        in_progress.dec()


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = get_request_id(request)
    observe_exception(
        exception_type=exc.__class__.__name__,
        error_code=exc.error_code,
        path=request.url.path,
        status_code=exc.status_code,
    )
    logger.warning(
        "application exception",
        extra=_request_log_extra(
            request,
            status_code=exc.status_code,
            error_code=exc.error_code,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
            request_id=request_id,
        ).model_dump(),
        headers={REQUEST_ID_HEADER: request_id, **exc.headers},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = get_request_id(request)
    observe_exception(
        exception_type=exc.__class__.__name__,
        error_code=str(exc.status_code),
        path=request.url.path,
        status_code=exc.status_code,
    )
    logger.warning(
        "http exception",
        extra=_request_log_extra(
            request,
            status_code=exc.status_code,
            error_code=str(exc.status_code),
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=str(exc.status_code),
            message=str(exc.detail),
            path=request.url.path,
            request_id=request_id,
        ).model_dump(),
        headers={REQUEST_ID_HEADER: request_id},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = get_request_id(request)
    observe_exception(
        exception_type=exc.__class__.__name__,
        error_code="validation_error",
        path=request.url.path,
        status_code=422,
    )
    logger.warning(
        "validation exception",
        extra=_request_log_extra(
            request,
            status_code=422,
            error_code="validation_error",
        ),
    )
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="validation_error",
            message="The request payload is invalid.",
            path=request.url.path,
            request_id=request_id,
            details=list(exc.errors()),
        ).model_dump(),
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    return HealthResponse(status="ok")


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness_check():
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=ReadinessResponse, tags=["health"])
async def readiness_check():
    readiness = run_readiness_checks()
    if readiness.status != "ok":
        return JSONResponse(
            status_code=503,
            content=readiness.model_dump(),
        )
    return readiness


if settings.metrics.enabled:

    @app.get(settings.metrics.path, include_in_schema=settings.metrics.include_in_schema)
    async def metrics(request: Request) -> Response:
        if settings.metrics.auth_token:
            authorization = request.headers.get("authorization", "")
            expected = f"Bearer {settings.metrics.auth_token}"
            if authorization != expected:
                raise UnauthorizedException("Metrics authentication failed.")
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id(request)
    observe_exception(
        exception_type=exc.__class__.__name__,
        error_code="internal_server_error",
        path=request.url.path,
        status_code=500,
    )
    logger.exception(
        "unhandled exception",
        extra=_request_log_extra(
            request,
            status_code=500,
            error_code="internal_server_error",
        ),
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="internal_server_error",
            message="Internal Server Error. Please contact admin.",
            path=request.url.path,
            request_id=request_id,
        ).model_dump(),
        headers={REQUEST_ID_HEADER: request_id},
    )
