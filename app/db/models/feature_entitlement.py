from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.account import Account
    from app.db.models.usage_event import UsageEvent
    from app.db.models.usage_reservation import UsageReservation


class FeatureEntitlement(SQLModel, table=True):
    __tablename__ = "feature_entitlement"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    resource_key: str = Field(index=True, max_length=100)
    units_total: int = Field(default=0)
    units_used: int = Field(default=0)
    status: str = Field(default="active", index=True, max_length=30)
    valid_from: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    valid_until: datetime | None = Field(default=None, index=True)
    source_type: str = Field(default="purchase", max_length=30)
    source_id: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    account: "Account" = Relationship(back_populates="entitlements")
    reservations: list["UsageReservation"] = Relationship(back_populates="entitlement")
    usage_events: list["UsageEvent"] = Relationship(back_populates="entitlement")
