from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.errors import unwrap_result
from app.core.config import settings
from app.core.exceptions import ForbiddenException
from app.core.request import get_request_id
from app.db.models.user import User as UserModel
from app.db.session import get_session
from app.schemas.user import UserCreate, UserPublic
from app.services.user_service import create_user, get_user_by_id

router = APIRouter()


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(
    request: Request,
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    if not settings.api.public_registration_enabled:
        raise ForbiddenException("Public registration is disabled.")
    return unwrap_result(
        create_user(
            session=session,
            user_in=user_in,
            request_id=get_request_id(request),
        )
    )


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.id != user_id and not current_user.is_ops_admin:
        raise ForbiddenException("You do not have permission to access this user.")
    return unwrap_result(get_user_by_id(session=session, user_id=user_id))
