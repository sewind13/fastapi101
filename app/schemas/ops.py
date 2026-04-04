from datetime import datetime

from pydantic import BaseModel

from app.schemas.billing import FeatureBalanceResponse


class OutboxSummaryResponse(BaseModel):
    pending: int
    published: int
    failed: int
    total: int


class OutboxEventResponse(BaseModel):
    id: int
    task_id: str
    task_name: str
    status: str
    attempts: int
    available_at: datetime
    published_at: datetime | None = None
    last_error: str | None = None


class DeadLetterReplayResponse(BaseModel):
    replayed: int


class UserAuthStateResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    failed_login_attempts: int
    locked_until: datetime | None = None
    is_locked: bool


class AccountEntitlementBalanceResponse(FeatureBalanceResponse):
    pass
