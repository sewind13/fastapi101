from fastapi import status


class AppException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        error_code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.headers = headers or {}
        super().__init__(message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="unauthorized",
            message=message,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="forbidden",
            message=message,
        )


class TooManyRequestsException(AppException):
    def __init__(
        self,
        message: str = "Too many requests.",
        *,
        error_code: str = "too_many_requests",
        retry_after_seconds: int | None = None,
    ):
        headers = {}
        if retry_after_seconds is not None:
            headers["Retry-After"] = str(retry_after_seconds)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code,
            message=message,
            headers=headers,
        )
