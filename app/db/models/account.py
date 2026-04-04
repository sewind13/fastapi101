from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.feature_entitlement import FeatureEntitlement
    from app.db.models.usage_event import UsageEvent
    from app.db.models.usage_reservation import UsageReservation
    from app.db.models.user import User


class Account(SQLModel, table=True):
    __tablename__ = "account"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=120)
    status: str = Field(default="active", index=True, max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    users: list["User"] = Relationship(back_populates="account")
    entitlements: list["FeatureEntitlement"] = Relationship(back_populates="account")
    usage_reservations: list["UsageReservation"] = Relationship(back_populates="account")
    usage_events: list["UsageEvent"] = Relationship(back_populates="account")
