from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    title: str = Field(..., examples=["Example item"], min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ItemCreate(ItemBase):
    pass


class ItemPublic(ItemBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
