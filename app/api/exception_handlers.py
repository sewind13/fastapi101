from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from app.core.exceptions import AppException
from app.core.logging import logger
from app.core.metrics import observe_exception
from app.core.middleware import request_log_extra
from app.core.request import REQUEST_ID_HEADER, get_request_id
from app.schemas.common import ErrorResponse


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
        extra=request_log_extra(
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
        extra=request_log_extra(
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
        extra=request_log_extra(
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
        extra=request_log_extra(
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


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, cast(ExceptionHandler, app_exception_handler))
    app.add_exception_handler(
        StarletteHTTPException, cast(ExceptionHandler, http_exception_handler)
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_exception_handler),
    )
    app.add_exception_handler(Exception, global_exception_handler)
