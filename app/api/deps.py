from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logging import log_audit_event
from app.core.request import get_request_id
from app.core.security import decode_token
from app.db.models.user import User as UserModel
from app.db.repositories.user import get_user_by_id
from app.db.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api.v1_prefix}/auth/login")

def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> UserModel:
    try:
        token_data = decode_token(token)
        if token_data.token_type != "access":
            raise UnauthorizedException()
    except Exception as exc:
        raise UnauthorizedException() from exc

    try:
        user_id = int(token_data.sub)
    except ValueError as exc:
        raise UnauthorizedException() from exc
    user = get_user_by_id(session=session, user_id=user_id)
    if user is None:
        raise UnauthorizedException()
    if not user.is_active:
        log_audit_event(
            "auth.access_blocked.inactive_user",
            event_type="auth",
            request_id=get_request_id(request),
            path=request.url.path,
            method=request.method,
            user_id=user.id,
            username=user.username,
            error_code="auth.inactive_user",
        )
        raise ForbiddenException("This account is inactive.")

    return user


def get_operations_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not settings.ops.enabled:
        raise ForbiddenException("Operations endpoints are disabled.")
    if not current_user.is_ops_admin:
        raise ForbiddenException("You do not have permission to access operations endpoints.")
    return current_user
