from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RevokedToken(SQLModel, table=True):
    __tablename__ = "revoked_token"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(index=True, unique=True, max_length=64)
    token_type: str = Field(max_length=20)
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
