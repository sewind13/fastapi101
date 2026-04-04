from sqlmodel import Session

from app.core.cache import cached_json, delete_prefix
from app.core.config import settings
from app.db.models.item import Item
from app.db.models.user import User as UserModel
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.item import add_item, list_items_by_owner_id
from app.schemas.item import ItemCreate
from app.services.entitlement_service import (
    commit_reserved_usage,
    release_reserved_usage,
    reserve_feature_usage,
)
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult

ITEMS_CREATE_FEATURE_KEY = "items.create"


def _items_cache_key(*, owner_id: int, offset: int, limit: int) -> str:
    return f"items:owner:{owner_id}:offset:{offset}:limit:{limit}"


def _items_cache_prefix(*, owner_id: int) -> str:
    return f"items:owner:{owner_id}:"


class ItemService(BaseService):
    def create_item_for_user(
        self,
        session: Session,
        item_in: ItemCreate,
        current_user: UserModel,
        request_id: str,
    ) -> ServiceResult[Item]:
        assert current_user.id is not None
        if current_user.account_id is None:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "The current user is not linked to an account.",
            )

        reservation_result = reserve_feature_usage(
            session,
            account_id=current_user.account_id,
            feature_key=ITEMS_CREATE_FEATURE_KEY,
            user_id=current_user.id,
            request_id=request_id,
        )
        if not reservation_result.ok or reservation_result.value is None:
            return ServiceResult(error=reservation_result.error)

        reservation = reservation_result.value
        db_item = Item.model_validate(item_in, update={"owner_id": current_user.id})

        try:
            created_item = add_item(session=session, item=db_item)
        except RepositoryError:
            release_reserved_usage(session, reservation_id=reservation.id or 0)
            return self.failure(
                ErrorCode.ITEM_PERSIST_FAILED,
                "Unable to save the example item right now.",
            )

        commit_result = commit_reserved_usage(
            session,
            reservation_id=reservation.id or 0,
        )
        if not commit_result.ok:
            return ServiceResult(error=commit_result.error)

        try:
            delete_prefix(_items_cache_prefix(owner_id=current_user.id), cache_name="items_list")
            return self.success(created_item)
        except RepositoryError:
            return self.failure(
                ErrorCode.ITEM_PERSIST_FAILED,
                "Unable to save the example item right now.",
            )

    def list_items_for_user(
        self, session: Session, current_user: UserModel, offset: int = 0, limit: int = 100
    ) -> ServiceResult[list[Item]]:
        assert current_user.id is not None
        owner_id = current_user.id
        cache_key = _items_cache_key(owner_id=owner_id, offset=offset, limit=limit)
        items = cached_json(
            cache_key,
            cache_name="items_list",
            loader=lambda: list_items_by_owner_id(
                session=session,
                owner_id=owner_id,
                offset=offset,
                limit=limit,
            ),
            serializer=lambda value: [item.model_dump(mode="json") for item in value],
            deserializer=lambda value: [Item.model_validate(item) for item in value],
            ttl_seconds=settings.cache.items_list_ttl_seconds,
        )
        return self.success(items)


def create_item_for_user(
    session: Session,
    item_in: ItemCreate,
    current_user: UserModel,
    request_id: str,
) -> ServiceResult[Item]:
    service = ItemService()
    return service.create_item_for_user(
        session=session,
        item_in=item_in,
        current_user=current_user,
        request_id=request_id,
    )


def list_items_for_user(
    session: Session, current_user: UserModel, offset: int = 0, limit: int = 100
) -> ServiceResult[list[Item]]:
    service = ItemService()
    return service.list_items_for_user(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )
