import json
from typing import cast

from app.core.config import settings
from app.worker.outbox import (
    build_password_reset_email_outbox_event,
    build_user_registered_outbox_event,
    build_verification_email_outbox_event,
    build_welcome_email_outbox_event,
    build_worker_failure_alert_outbox_event,
)
from app.worker.publisher import publish_task
from app.worker.schemas import (
    PasswordResetEmailPayload,
    UserRegisteredPayload,
    VerificationEmailPayload,
    WelcomeEmailPayload,
    WorkerFailureAlertPayload,
)


class FakeChannel:
    def __init__(self):
        self.declared_queues: list[tuple[str, bool, dict[str, object] | None, bool]] = []
        self.published_messages: list[dict[str, object]] = []
        self.queue_depths = {
            "app.default": 1,
            "app.default.retry": 0,
            "app.default.dlq": 0,
        }

    def queue_declare(
        self,
        *,
        queue: str,
        durable: bool = True,
        arguments: dict[str, object] | None = None,
        passive: bool = False,
    ):
        self.declared_queues.append((queue, durable, arguments, passive))

        class Method:
            message_count = self.queue_depths.get(queue, 0)

        class Result:
            method = Method()

        return Result()

    def basic_publish(self, *, exchange: str, routing_key: str, body: bytes, properties):
        self.published_messages.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "properties": properties,
            }
        )


class FakeConnection:
    def __init__(self):
        self.channel_instance = FakeChannel()
        self.closed = False

    def channel(self):
        return self.channel_instance

    def close(self):
        self.closed = True


def test_publish_task_returns_false_when_worker_is_disabled(monkeypatch):
    monkeypatch.setattr(settings.worker, "enabled", False)
    monkeypatch.setattr(settings.worker, "broker_url", None)

    published = publish_task(task_name="user.registered", payload={"user_id": 1})

    assert published is False


def test_publish_task_sends_durable_message(monkeypatch):
    fake_connection = FakeConnection()

    monkeypatch.setattr(settings.worker, "enabled", True)
    monkeypatch.setattr(settings.worker, "broker_url", "amqp://guest:guest@queue:5672/")
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")
    monkeypatch.setattr(settings.worker, "retry_delay_ms", 30000)

    monkeypatch.setattr("app.worker.publisher.pika.URLParameters", lambda url: url)
    monkeypatch.setattr(
        "app.worker.publisher.pika.BlockingConnection",
        lambda parameters: fake_connection,
    )

    published = publish_task(
        task_name="user.registered",
        payload={"user_id": 1, "username": "alice"},
        request_id="req-123",
    )

    assert published is True
    assert fake_connection.channel_instance.declared_queues[:3] == [
        ("app.default.dlq", True, None, False),
        (
            "app.default.retry",
            True,
            {
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "app.default",
            },
            False,
        ),
        ("app.default", True, None, False),
    ]
    assert len(fake_connection.channel_instance.published_messages) == 1
    message = fake_connection.channel_instance.published_messages[0]
    assert message["routing_key"] == "app.default"
    body = json.loads(cast(bytes, message["body"]).decode("utf-8"))
    assert body["task"] == "user.registered"
    assert body["payload"]["user_id"] == 1
    assert body["metadata"]["request_id"] == "req-123"
    assert body["metadata"]["task_id"]
    assert fake_connection.closed is True


def test_build_user_registered_outbox_event_uses_payload_schema():
    event = build_user_registered_outbox_event(
        payload=UserRegisteredPayload(user_id=None, username="alice", email="user@example.com"),
        request_id="req-123",
        source="api.users.register",
    )

    assert event.task_name == "user.registered"
    assert event.payload["username"] == "alice"
    assert event.source == "api.users.register"


def test_build_welcome_email_outbox_event_uses_payload_schema():
    event = build_welcome_email_outbox_event(
        payload=WelcomeEmailPayload(user_id=None, username="alice", email="user@example.com"),
        request_id="req-456",
        source="api.users.register",
    )

    assert event.task_name == "email.send_welcome"
    assert event.payload["email"] == "user@example.com"
    assert event.task_id


def test_build_password_reset_email_outbox_event_uses_payload_schema():
    event = build_password_reset_email_outbox_event(
        payload=PasswordResetEmailPayload(
            user_id=None,
            username="alice",
            email="user@example.com",
            reset_url="https://example.com/reset/token",
        ),
        request_id="req-789",
        source="api.auth.password_reset",
    )

    assert event.task_name == "email.send_password_reset"
    assert event.payload["reset_url"] == "https://example.com/reset/token"


def test_build_verification_email_outbox_event_uses_payload_schema():
    event = build_verification_email_outbox_event(
        payload=VerificationEmailPayload(
            user_id=None,
            username="alice",
            email="user@example.com",
            verification_url="https://example.com/verify/token",
        ),
        request_id="req-999",
        source="api.auth.verify_email",
    )

    assert event.task_name == "email.send_verification"
    assert event.payload["verification_url"] == "https://example.com/verify/token"


def test_build_worker_failure_alert_outbox_event_uses_payload_schema():
    event = build_worker_failure_alert_outbox_event(
        payload=WorkerFailureAlertPayload(
            task_name="email.send_verification",
            task_id="task-123",
            error_message="SMTP timeout",
        ),
        request_id="req-worker",
        source="worker",
    )

    assert event.task_name == "webhook.worker_failure_alert"
    assert event.payload["task_id"] == "task-123"
    assert event.payload["error_message"] == "SMTP timeout"
