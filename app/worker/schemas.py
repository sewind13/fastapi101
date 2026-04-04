from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str | None = None
    source: str = "app"
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TaskEnvelope(BaseModel):
    task: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: TaskMetadata = Field(default_factory=TaskMetadata)


class UserRegisteredPayload(BaseModel):
    user_id: int | None
    username: str
    email: str


class WelcomeEmailPayload(BaseModel):
    user_id: int | None
    email: str
    username: str


class PasswordResetEmailPayload(BaseModel):
    user_id: int | None
    email: str
    username: str
    reset_url: str


class VerificationEmailPayload(BaseModel):
    user_id: int | None
    email: str
    username: str
    verification_url: str


class WorkerFailureAlertPayload(BaseModel):
    task_name: str
    task_id: str
    error_message: str


KnownTaskName = Literal[
    "user.registered",
    "email.send_welcome",
    "email.send_password_reset",
    "email.send_verification",
    "webhook.user_registered",
    "webhook.worker_failure_alert",
]


def parse_task_payload(task_name: str, payload: dict[str, Any]) -> BaseModel:
    if task_name == "user.registered":
        return UserRegisteredPayload.model_validate(payload)
    if task_name == "email.send_welcome":
        return WelcomeEmailPayload.model_validate(payload)
    if task_name == "email.send_password_reset":
        return PasswordResetEmailPayload.model_validate(payload)
    if task_name == "email.send_verification":
        return VerificationEmailPayload.model_validate(payload)
    if task_name == "webhook.user_registered":
        return UserRegisteredPayload.model_validate(payload)
    if task_name == "webhook.worker_failure_alert":
        return WorkerFailureAlertPayload.model_validate(payload)
    raise ValueError(f"Unknown worker task: {task_name}")
