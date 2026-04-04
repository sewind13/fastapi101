from sqlmodel import Session, select

from app.db.models.item import Item
from app.db.repositories.base import BaseRepository
from app.db.repositories.exceptions import RepositoryError


def add_item(session: Session, item: Item) -> Item:
    try:
        session.add(item)
        session.flush()
        session.refresh(item)
        return item
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to stage item") from exc


def create_item(session: Session, item: Item) -> Item:
    try:
        return BaseRepository[Item](session).save(item)
    except Exception as exc:
        raise RepositoryError("Failed to persist item") from exc


def list_items_by_owner_id(
    session: Session, owner_id: int, offset: int = 0, limit: int = 100
) -> list[Item]:
    statement = select(Item).where(Item.owner_id == owner_id).offset(offset).limit(limit)
    return list(session.exec(statement).all())
