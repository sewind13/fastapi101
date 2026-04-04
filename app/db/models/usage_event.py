from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.account import Account
    from app.db.models.feature_entitlement import FeatureEntitlement
    from app.db.models.usage_reservation import UsageReservation


class UsageEvent(SQLModel, table=True):
    __tablename__ = "usage_event"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    entitlement_id: int = Field(foreign_key="feature_entitlement.id", index=True)
    reservation_id: int | None = Field(default=None, foreign_key="usage_reservation.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    resource_key: str = Field(index=True, max_length=100)
    feature_key: str = Field(index=True, max_length=120)
    units: int = Field(default=1)
    request_id: str = Field(index=True, max_length=120)
    status: str = Field(default="committed", index=True, max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    account: "Account" = Relationship(back_populates="usage_events")
    entitlement: "FeatureEntitlement" = Relationship(back_populates="usage_events")
    reservation: "UsageReservation" = Relationship(back_populates="usage_events")
