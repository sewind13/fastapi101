from sqlmodel import Session, col, select

from app.db.models.item import Item
from app.db.repositories.base import BaseRepository
from app.db.repositories.exceptions import RepositoryError


def add_item(session: Session, item: Item) -> Item:
    """Stage a new item inside the current transaction without committing it.

    This helper is useful when the caller needs the row to be flushed and
    refreshed, but still wants to commit later as part of a larger atomic flow.
    """

    try:
        session.add(item)
        session.flush()
        session.refresh(item)
        return item
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to stage item") from exc


def save_item(session: Session, item: Item) -> Item:
    """Persist an item using the repository save flow and commit the change.

    Use this when the caller wants the item write to be finalized in this step
    rather than staged for a later commit.
    """

    try:
        return BaseRepository[Item](session).save(item)
    except Exception as exc:
        raise RepositoryError("Failed to persist item") from exc


def list_items_by_owner_id(
    session: Session,
    owner_id: int,
    offset: int = 0,
    limit: int = 100,
    include_archived: bool = False,
) -> list[Item]:
    """List items for one owner, optionally including archived rows."""

    statement = select(Item).where(Item.owner_id == owner_id)
    if not include_archived:
        statement = statement.where(col(Item.is_archived).is_(False))

    statement = statement.offset(offset).limit(limit)

    return list(session.exec(statement).all())


def get_item_by_id(session: Session, item_id: int) -> Item | None:
    """Return a single item by primary key, or ``None`` when it is missing."""

    statement = select(Item).where(Item.id == item_id)
    return session.exec(statement).first()
