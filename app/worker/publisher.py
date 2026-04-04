import pika  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import observe_worker_queue_depth
from app.db.models.user import User
from app.worker.schemas import (
    PasswordResetEmailPayload,
    TaskEnvelope,
    TaskMetadata,
    UserRegisteredPayload,
    VerificationEmailPayload,
    WelcomeEmailPayload,
    WorkerFailureAlertPayload,
)


def _worker_is_configured() -> bool:
    return settings.worker.enabled and bool(settings.worker.broker_url)


def ensure_worker_topology(channel) -> None:
    channel.queue_declare(queue=settings.worker.dead_letter_queue_name, durable=True)
    channel.queue_declare(
        queue=settings.worker.retry_queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": settings.worker.queue_name,
        },
    )
    channel.queue_declare(queue=settings.worker.queue_name, durable=True)


def _observe_queue_depths(channel) -> None:
    for queue_name in (
        settings.worker.queue_name,
        settings.worker.retry_queue_name,
        settings.worker.dead_letter_queue_name,
    ):
        result = channel.queue_declare(queue=queue_name, passive=True)
        message_count = int(getattr(result.method, "message_count", 0))
        observe_worker_queue_depth(queue_name=queue_name, depth=message_count)


def publish_envelope(*, envelope: TaskEnvelope) -> bool:
    if not _worker_is_configured():
        return False

    parameters = pika.URLParameters(settings.worker.broker_url or "")
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        ensure_worker_topology(channel)
        channel.basic_publish(
            exchange="",
            routing_key=settings.worker.queue_name,
            body=envelope.model_dump_json().encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
        _observe_queue_depths(channel)
    finally:
        connection.close()

    logger.info(
        "published background task",
        extra={
            "event_type": "worker",
            "task_name": envelope.task,
            "request_id": envelope.metadata.request_id,
        },
    )
    return True


def publish_task(
    *,
    task_name: str,
    payload: dict[str, object],
    request_id: str | None = None,
    source: str = "api",
) -> bool:
    envelope = TaskEnvelope(
        task=task_name,
        payload=payload,
        metadata=TaskMetadata(request_id=request_id, source=source),
    )
    return publish_envelope(envelope=envelope)


def publish_user_registered_event(*, user: User, request_id: str | None = None) -> bool:
    payload = UserRegisteredPayload(
        user_id=user.id,
        username=user.username,
        email=user.email,
    )
    return publish_task(
        task_name="user.registered",
        payload=payload.model_dump(),
        request_id=request_id,
        source="api.users.register",
    )


def publish_welcome_email_task(*, user: User, request_id: str | None = None) -> bool:
    payload = WelcomeEmailPayload(
        user_id=user.id,
        email=user.email,
        username=user.username,
    )
    return publish_task(
        task_name="email.send_welcome",
        payload=payload.model_dump(),
        request_id=request_id,
        source="api.users.register",
    )


def publish_user_registered_webhook_task(*, user: User, request_id: str | None = None) -> bool:
    payload = UserRegisteredPayload(
        user_id=user.id,
        username=user.username,
        email=user.email,
    )
    return publish_task(
        task_name="webhook.user_registered",
        payload=payload.model_dump(),
        request_id=request_id,
        source="api.users.register",
    )


def publish_password_reset_email_task(
    *,
    user: User,
    reset_url: str,
    request_id: str | None = None,
) -> bool:
    payload = PasswordResetEmailPayload(
        user_id=user.id,
        email=user.email,
        username=user.username,
        reset_url=reset_url,
    )
    return publish_task(
        task_name="email.send_password_reset",
        payload=payload.model_dump(),
        request_id=request_id,
        source="api.auth.password_reset",
    )


def publish_verification_email_task(
    *,
    user: User,
    verification_url: str,
    request_id: str | None = None,
) -> bool:
    payload = VerificationEmailPayload(
        user_id=user.id,
        email=user.email,
        username=user.username,
        verification_url=verification_url,
    )
    return publish_task(
        task_name="email.send_verification",
        payload=payload.model_dump(),
        request_id=request_id,
        source="api.auth.verify_email",
    )


def publish_worker_failure_alert_task(
    *,
    task_name: str,
    task_id: str,
    error_message: str,
    request_id: str | None = None,
) -> bool:
    payload = WorkerFailureAlertPayload(
        task_name=task_name,
        task_id=task_id,
        error_message=error_message,
    )
    return publish_task(
        task_name="webhook.worker_failure_alert",
        payload=payload.model_dump(),
        request_id=request_id,
        source="worker",
    )
