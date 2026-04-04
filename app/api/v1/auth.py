from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.errors import unwrap_result
from app.core.logging import log_audit_event
from app.core.metrics import observe_auth_event
from app.core.rate_limit import (
    check_login_rate_limit,
    check_token_rate_limit,
    record_login_attempt,
)
from app.core.request import get_request_id
from app.db.models.user import User as UserModel
from app.db.session import get_session
from app.schemas.common import MessageResponse
from app.schemas.token import (
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenPair,
)
from app.schemas.user import UserPublic
from app.services.auth_service import (
    authenticate_user,
    confirm_email_verification,
    confirm_password_reset,
    logout_refresh_token,
    refresh_tokens,
    request_email_verification,
    request_password_reset,
)

router = APIRouter()


@router.post("/login", response_model=TokenPair)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    rate_limit_error = check_login_rate_limit(request, form_data.username)
    if rate_limit_error is not None:
        observe_auth_event(event="login", outcome="rate_limited")
        log_audit_event(
            "auth.login.rate_limited",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            username=form_data.username,
            error_code=rate_limit_error.error_code,
        )
        raise rate_limit_error

    result = authenticate_user(
        session=session,
        username=form_data.username,
        password=form_data.password,
    )
    rate_limit_error = record_login_attempt(
        request,
        form_data.username,
        success=result.ok,
    )
    if rate_limit_error is not None:
        observe_auth_event(event="login", outcome="rate_limited")
        log_audit_event(
            "auth.login.rate_limited",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            username=form_data.username,
            error_code=rate_limit_error.error_code,
        )
        raise rate_limit_error

    if result.ok:
        observe_auth_event(event="login", outcome="succeeded")
        log_audit_event(
            "auth.login.succeeded",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            username=form_data.username,
            token_type="access_refresh_pair",
        )
    else:
        error = result.error
        outcome = "locked" if error and error.code == "auth.account_locked" else "failed"
        event_name = "auth.login.locked" if outcome == "locked" else "auth.login.failed"
        observe_auth_event(event="login", outcome=outcome)
        log_audit_event(
            event_name,
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            username=form_data.username,
            error_code=error.code if error else "unknown_error",
        )
    return unwrap_result(result)


@router.post("/refresh", response_model=TokenPair)
def refresh_access_token(
    request: Request,
    payload: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    rate_limit_error = check_token_rate_limit(request, "auth.refresh")
    if rate_limit_error is not None:
        observe_auth_event(event="refresh", outcome="rate_limited")
        log_audit_event(
            "auth.refresh.rate_limited",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
            error_code=rate_limit_error.error_code,
        )
        raise rate_limit_error

    result = refresh_tokens(session=session, refresh_token=payload.refresh_token)
    if result.ok:
        observe_auth_event(event="refresh", outcome="succeeded")
        log_audit_event(
            "auth.refresh.succeeded",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
        )
    else:
        observe_auth_event(event="refresh", outcome="failed")
        error = result.error
        log_audit_event(
            "auth.refresh.failed",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
            error_code=error.code if error else "unknown_error",
        )
    return unwrap_result(result)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    payload: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    rate_limit_error = check_token_rate_limit(request, "auth.logout")
    if rate_limit_error is not None:
        observe_auth_event(event="logout", outcome="rate_limited")
        log_audit_event(
            "auth.logout.rate_limited",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
            error_code=rate_limit_error.error_code,
        )
        raise rate_limit_error

    result = logout_refresh_token(session=session, refresh_token=payload.refresh_token)
    if result.ok:
        observe_auth_event(event="logout", outcome="succeeded")
        log_audit_event(
            "auth.logout.succeeded",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
        )
    else:
        observe_auth_event(event="logout", outcome="failed")
        error = result.error
        log_audit_event(
            "auth.logout.failed",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            token_type="refresh",
            error_code=error.code if error else "unknown_error",
        )
    return MessageResponse(message=unwrap_result(result))


@router.post("/verify-email/request", response_model=MessageResponse)
def request_verification_email(
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    message = unwrap_result(
        request_email_verification(session=session, user=current_user)
    )
    return MessageResponse(message=message)


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset_email(
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    message = unwrap_result(request_password_reset(session=session, email=payload.email))
    return MessageResponse(message=message)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset_route(
    payload: PasswordResetConfirmRequest,
    session: Session = Depends(get_session),
):
    message = unwrap_result(
        confirm_password_reset(
            session=session,
            token=payload.token,
            new_password=payload.new_password,
        )
    )
    return MessageResponse(message=message)


@router.get("/verify-email/confirm", response_model=MessageResponse)
def confirm_verification_email(
    token: str,
    session: Session = Depends(get_session),
):
    message = unwrap_result(confirm_email_verification(session=session, token=token))
    return MessageResponse(message=message)


@router.get("/me", response_model=UserPublic)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    return current_user
