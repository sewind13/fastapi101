from fastapi import status

from app.core.exceptions import AppException
from app.services.exceptions import ErrorCode
from app.services.result import ServiceResult

ERROR_STATUS_MAP = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_ACCOUNT_LOCKED: status.HTTP_423_LOCKED,
    ErrorCode.AUTH_EMAIL_NOT_VERIFIED: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTH_INACTIVE_USER: status.HTTP_403_FORBIDDEN,
    ErrorCode.AUTH_INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_REFRESH_REUSED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.AUTH_RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.INFRA_DB_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.SECURITY_WEAK_PASSWORD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BILLING_NO_ENTITLEMENT: status.HTTP_403_FORBIDDEN,
    ErrorCode.BILLING_QUOTA_EXHAUSTED: status.HTTP_403_FORBIDDEN,
    ErrorCode.BILLING_ENTITLEMENT_EXPIRED: status.HTTP_403_FORBIDDEN,
    ErrorCode.BILLING_FEATURE_NOT_ENABLED: status.HTTP_403_FORBIDDEN,
    ErrorCode.BILLING_INVALID_ENTITLEMENT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BILLING_RESERVATION_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.BILLING_INVALID_RESERVATION_STATE: status.HTTP_409_CONFLICT,
    ErrorCode.USER_CONFLICT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ITEM_PERSIST_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.COMMON_INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.ITEM_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ITEM_FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.ITEM_ALREADY_ARCHIVED: status.HTTP_409_CONFLICT,
}


def unwrap_result(result: ServiceResult):
    if result.ok:
        return result.value

    error = result.error
    if error is None:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.COMMON_INTERNAL_ERROR,
            message="Unexpected empty service error",
        )

    raise AppException(
        status_code=ERROR_STATUS_MAP.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        error_code=error.code,
        message=error.message,
    )
