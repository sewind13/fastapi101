from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.user import User

class Item(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=255)
    description: str | None = None

    owner_id: int = Field(foreign_key="user.id", index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    owner: Optional["User"] = Relationship(back_populates="items")

    is_archived: bool = Field(default=False, nullable=False)
    archived_at: datetime | None = Field(default=None, nullable=True)

    restored_at: datetime | None = Field(default=None, nullable=True)
    restore_count: int = Field(default=0, nullable=False)

