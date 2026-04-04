from pydantic import BaseModel

from app.db.models.outbox_event import OutboxEvent
from app.worker.schemas import (
    PasswordResetEmailPayload,
    TaskEnvelope,
    TaskMetadata,
    UserRegisteredPayload,
    VerificationEmailPayload,
    WelcomeEmailPayload,
    WorkerFailureAlertPayload,
)


def build_outbox_event(
    *,
    task_name: str,
    payload: BaseModel,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    envelope = TaskEnvelope(
        task=task_name,
        payload=payload.model_dump(),
        metadata=TaskMetadata(request_id=request_id, source=source),
    )
    return OutboxEvent(
        task_id=envelope.metadata.task_id,
        task_name=envelope.task,
        payload=envelope.payload,
        source=envelope.metadata.source,
    )


def build_user_registered_outbox_event(
    *,
    payload: UserRegisteredPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="user.registered",
        payload=payload,
        request_id=request_id,
        source=source,
    )


def build_welcome_email_outbox_event(
    *,
    payload: WelcomeEmailPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="email.send_welcome",
        payload=payload,
        request_id=request_id,
        source=source,
    )


def build_user_registered_webhook_outbox_event(
    *,
    payload: UserRegisteredPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="webhook.user_registered",
        payload=payload,
        request_id=request_id,
        source=source,
    )


def build_password_reset_email_outbox_event(
    *,
    payload: PasswordResetEmailPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="email.send_password_reset",
        payload=payload,
        request_id=request_id,
        source=source,
    )


def build_verification_email_outbox_event(
    *,
    payload: VerificationEmailPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="email.send_verification",
        payload=payload,
        request_id=request_id,
        source=source,
    )


def build_worker_failure_alert_outbox_event(
    *,
    payload: WorkerFailureAlertPayload,
    request_id: str | None,
    source: str,
) -> OutboxEvent:
    return build_outbox_event(
        task_name="webhook.worker_failure_alert",
        payload=payload,
        request_id=request_id,
        source=source,
    )
