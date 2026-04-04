from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.errors import unwrap_result
from app.core.request import get_request_id
from app.db.models.user import User as UserModel
from app.db.session import get_session
from app.schemas.item import ItemCreate, ItemPublic
from app.services.item_service import create_item_for_user, list_items_for_user

router = APIRouter()


@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    request: Request,
    item_in: ItemCreate,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    return unwrap_result(
        create_item_for_user(
            session=session,
            item_in=item_in,
            current_user=current_user,
            request_id=get_request_id(request),
        )
    )

@router.get("/", response_model=list[ItemPublic])
def read_items(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    return unwrap_result(
        list_items_for_user(
            session=session,
            current_user=current_user,
            offset=offset,
            limit=limit,
        )
    )

@router.get("/me", response_model=list[ItemPublic])
def read_my_items(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    return unwrap_result(
        list_items_for_user(
            session=session,
            current_user=current_user,
            offset=offset,
            limit=limit,
        )
    )

@router.get("/me-fast", response_model=list[ItemPublic])
def read_my_items_relationship(
    *,
    current_user: UserModel = Depends(get_current_user),
    offset: int = 0,
    limit: int = Query(default=10, le=100),
):
    return current_user.items[offset : offset + limit]
