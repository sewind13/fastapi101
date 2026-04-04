from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.logging import logger
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)
from app.services.webhook_service import send_user_registered_webhook, send_worker_failure_alert
from app.worker.schemas import (
    PasswordResetEmailPayload,
    TaskEnvelope,
    UserRegisteredPayload,
    VerificationEmailPayload,
    WelcomeEmailPayload,
    WorkerFailureAlertPayload,
    parse_task_payload,
)

TaskHandler = Callable[[Any], None]
TASK_REGISTRY: dict[str, TaskHandler] = {}


@dataclass(frozen=True)
class TaskRetryPolicy:
    max_retries: int
    base_delay_ms: int
    max_delay_ms: int


DEFAULT_TASK_RETRY_POLICY = TaskRetryPolicy(
    max_retries=3,
    base_delay_ms=30_000,
    max_delay_ms=300_000,
)
TASK_RETRY_POLICIES: dict[str, TaskRetryPolicy] = {
    "user.registered": TaskRetryPolicy(max_retries=2, base_delay_ms=5_000, max_delay_ms=30_000),
    "email.send_welcome": TaskRetryPolicy(
        max_retries=5,
        base_delay_ms=30_000,
        max_delay_ms=600_000,
    ),
    "webhook.user_registered": TaskRetryPolicy(
        max_retries=6,
        base_delay_ms=60_000,
        max_delay_ms=900_000,
    ),
    "email.send_password_reset": TaskRetryPolicy(
        max_retries=5,
        base_delay_ms=30_000,
        max_delay_ms=600_000,
    ),
    "email.send_verification": TaskRetryPolicy(
        max_retries=5,
        base_delay_ms=30_000,
        max_delay_ms=600_000,
    ),
    "webhook.worker_failure_alert": TaskRetryPolicy(
        max_retries=8,
        base_delay_ms=60_000,
        max_delay_ms=900_000,
    ),
}


def register_task(name: str) -> Callable[[TaskHandler], TaskHandler]:
    def decorator(func: TaskHandler) -> TaskHandler:
        TASK_REGISTRY[name] = func
        return func

    return decorator


def dispatch_envelope(envelope: TaskEnvelope) -> None:
    handler = TASK_REGISTRY.get(envelope.task)
    if handler is None:
        raise ValueError(f"Unknown worker task: {envelope.task}")
    parsed_payload = parse_task_payload(envelope.task, envelope.payload)
    handler(parsed_payload)


def dispatch_task(task_name: str, payload: dict[str, Any]) -> None:
    dispatch_envelope(TaskEnvelope(task=task_name, payload=payload))


def get_task_retry_policy(task_name: str) -> TaskRetryPolicy:
    return TASK_RETRY_POLICIES.get(task_name, DEFAULT_TASK_RETRY_POLICY)


@register_task("user.registered")
def handle_user_registered(payload: UserRegisteredPayload) -> None:
    logger.info(
        "processed background task user.registered",
        extra={
            "event_type": "worker",
            "user_id": payload.user_id,
            "username": payload.username,
        },
    )


@register_task("email.send_welcome")
def handle_send_welcome_email(payload: WelcomeEmailPayload) -> None:
    send_welcome_email(
        user_id=payload.user_id,
        email=payload.email,
        username=payload.username,
    )


@register_task("webhook.user_registered")
def handle_user_registered_webhook(payload: UserRegisteredPayload) -> None:
    send_user_registered_webhook(
        user_id=payload.user_id,
        username=payload.username,
        email=payload.email,
    )


@register_task("email.send_password_reset")
def handle_send_password_reset_email(payload: PasswordResetEmailPayload) -> None:
    send_password_reset_email(
        user_id=payload.user_id,
        email=payload.email,
        username=payload.username,
        reset_url=payload.reset_url,
    )


@register_task("email.send_verification")
def handle_send_verification_email(payload: VerificationEmailPayload) -> None:
    send_verification_email(
        user_id=payload.user_id,
        email=payload.email,
        username=payload.username,
        verification_url=payload.verification_url,
    )


@register_task("webhook.worker_failure_alert")
def handle_worker_failure_alert(payload: WorkerFailureAlertPayload) -> None:
    send_worker_failure_alert(
        task_name=payload.task_name,
        task_id=payload.task_id,
        error_message=payload.error_message,
    )
