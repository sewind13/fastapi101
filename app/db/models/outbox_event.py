from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class OutboxEvent(SQLModel, table=True):
    __tablename__ = "outbox_event"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True, max_length=64)
    task_name: str = Field(index=True, max_length=100)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    source: str = Field(default="app", max_length=100)
    status: str = Field(default="pending", index=True, max_length=20)
    attempts: int = Field(default=0)
    available_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None, max_length=500)
