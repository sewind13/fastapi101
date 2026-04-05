from datetime import UTC, datetime

from sqlmodel import Session

from app.core.cache import cached_json, delete_prefix
from app.core.config import settings
from app.db.models.item import Item
from app.db.models.user import User as UserModel
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.item import (
    add_item,
    get_item_by_id,
    list_items_by_owner_id,
    save_item,
)
from app.schemas.item import ItemCreate
from app.services.entitlement_service import (
    commit_reserved_usage,
    release_reserved_usage,
    reserve_feature_usage,
)
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult

ITEMS_CREATE_FEATURE_KEY = "items.create"
ITEMS_ARCHIVE_FEATURE_KEY = "items.archive"


def _items_cache_key(*, owner_id: int, offset: int, limit: int) -> str:
    """Build the cache key for one owner's paginated item list."""

    return f"items:owner:{owner_id}:offset:{offset}:limit:{limit}"


def _items_cache_prefix(*, owner_id: int) -> str:
    """Build the cache prefix used to invalidate one owner's item list cache."""

    return f"items:owner:{owner_id}:"


class ItemService(BaseService):
    def create_item_for_user(
        self,
        session: Session,
        item_in: ItemCreate,
        current_user: UserModel,
        request_id: str,
    ) -> ServiceResult[Item]:
        """Create an item for the current user and commit quota usage on success."""

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
            release_result = release_reserved_usage(session, reservation_id=reservation.id or 0)
            if not release_result.ok:
                return ServiceResult(error=release_result.error)
            return self.failure(
                ErrorCode.ITEM_PERSIST_FAILED,
                "Unable to save the example item right now.",
            )

        commit_result = commit_reserved_usage(
            session,
            reservation_id=reservation.id or 0,
        )
        if not commit_result.ok:
            session.rollback()
            return ServiceResult(error=commit_result.error)

        try:
            delete_prefix(_items_cache_prefix(owner_id=current_user.id), cache_name="items_list")
        except Exception:
            pass

        return self.success(created_item)

    def archive_item_for_user(
        self,
        session: Session,
        item_id: int,
        current_user: UserModel,
        request_id: str,
    ) -> ServiceResult[Item]:
        """Archive one item and charge archive usage only after a successful write."""

        assert current_user.id is not None

        item = get_item_by_id(session, item_id)
        if item is None:
            return self.failure(
                ErrorCode.ITEM_NOT_FOUND,
                "Item not found.",
            )

        if item.owner_id != current_user.id:
            return self.failure(
                ErrorCode.ITEM_FORBIDDEN,
                "You do not have access to archive this item.",
            )

        if item.is_archived:
            return self.failure(
                ErrorCode.ITEM_ALREADY_ARCHIVED,
                "Item is already archived.",
            )

        if current_user.account_id is None:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "The current user is not linked to an account.",
            )

        # Validate the item and ownership first, then reserve archive quota only for
        # requests that are actually allowed to perform the write.
        reservation_result = reserve_feature_usage(
            session,
            account_id=current_user.account_id,
            feature_key=ITEMS_ARCHIVE_FEATURE_KEY,
            user_id=current_user.id,
            request_id=request_id,
        )
        if not reservation_result.ok or reservation_result.value is None:
            return ServiceResult(error=reservation_result.error)

        reservation = reservation_result.value

        item.is_archived = True
        item.archived_at = datetime.now(UTC)

        try:
            saved_item = save_item(session, item)
        except RepositoryError:
            release_result = release_reserved_usage(session, reservation_id=reservation.id or 0)
            if not release_result.ok:
                return ServiceResult(error=release_result.error)
            return self.failure(
                ErrorCode.ITEM_PERSIST_FAILED,
                "Unable to archive the example item right now.",
            )

        # Only commit usage after the archive write succeeds, so failed writes do not
        # consume quota.
        commit_result = commit_reserved_usage(
            session,
            reservation_id=reservation.id or 0,
        )
        if not commit_result.ok:
            session.rollback()
            return ServiceResult(error=commit_result.error)

        try:
            delete_prefix(_items_cache_prefix(owner_id=current_user.id), cache_name="items_list")
        except Exception:
            pass

        return self.success(saved_item)

    def list_items_for_user(
        self, session: Session, current_user: UserModel, offset: int = 0, limit: int = 100
    ) -> ServiceResult[list[Item]]:
        """Return the current user's item list, using read-through cache when enabled."""

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
    """Convenience wrapper around ``ItemService.create_item_for_user``."""

    service = ItemService()
    return service.create_item_for_user(
        session=session,
        item_in=item_in,
        current_user=current_user,
        request_id=request_id,
    )


def archive_item_for_user(
    session: Session,
    item_id: int,
    current_user: UserModel,
    request_id: str,
) -> ServiceResult[Item]:
    """Convenience wrapper around ``ItemService.archive_item_for_user``."""

    service = ItemService()
    return service.archive_item_for_user(
        session=session,
        item_id=item_id,
        current_user=current_user,
        request_id=request_id,
    )


def list_items_for_user(
    session: Session, current_user: UserModel, offset: int = 0, limit: int = 100
) -> ServiceResult[list[Item]]:
    """Convenience wrapper around ``ItemService.list_items_for_user``."""

    service = ItemService()
    return service.list_items_for_user(
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
    )
