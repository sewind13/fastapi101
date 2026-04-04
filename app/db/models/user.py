from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.account import Account
    from app.db.models.item import Item


class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    account_id: int | None = Field(default=None, foreign_key="account.id", index=True)

    username: str = Field(index=True, unique=True, max_length=20)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str

    phone: str | None = Field(default=None)

    is_active: bool = Field(default=True)
    email_verified: bool = Field(default=False)
    role: str = Field(default="user", max_length=30)
    email_verification_sent_at: datetime | None = Field(default=None)
    failed_login_attempts: int = Field(default=0)
    locked_until: datetime | None = Field(default=None)

    account: "Account" = Relationship(back_populates="users")
    items: list["Item"] = Relationship(back_populates="owner")

    @property
    def is_ops_admin(self) -> bool:
        return self.role in {"ops_admin", "platform_admin"}
