from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Base schema for Item."""
    title: str = Field(..., examples=["Example item"], min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ItemCreate(ItemBase):
    """Schema for creating an Item."""
    pass


class ItemPublic(ItemBase):
    """Schema for displaying an Item."""
    id: int
    owner_id: int
    created_at: datetime

    is_archived: bool
    archived_at: datetime | None = None

    restored_at: datetime | None = None
    restore_count: int = 0

    model_config = ConfigDict(from_attributes=True)
