from types import SimpleNamespace
from typing import cast

from app.core.config import settings
from app.worker.runner import _extract_retry_count, _handle_delivery
from app.worker.schemas import TaskEnvelope
from app.worker.tasks import TaskRetryPolicy


class FakeChannel:
    def __init__(self):
        self.acked: list[int] = []
        self.nacked: list[tuple[int, bool]] = []
        self.published: list[dict[str, object]] = []
        self.declared: list[str] = []

    def basic_ack(self, *, delivery_tag: int):
        self.acked.append(delivery_tag)

    def basic_nack(self, *, delivery_tag: int, requeue: bool):
        self.nacked.append((delivery_tag, requeue))

    def basic_publish(self, *, exchange: str, routing_key: str, body: bytes, properties):
        self.published.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "properties": properties,
            }
        )

    def queue_declare(
        self,
        *,
        queue: str,
        durable: bool = True,
        arguments: dict[str, object] | None = None,
        passive: bool = False,
    ):
        del durable, arguments, passive
        self.declared.append(queue)
        return SimpleNamespace(method=SimpleNamespace(message_count=0))


def make_delivery(tag: int = 1):
    return SimpleNamespace(delivery_tag=tag)


def raise_task_failure(task, payload):
    del task, payload
    raise ValueError("boom")


def raise_envelope_failure(envelope):
    del envelope
    raise ValueError("boom")


def test_extract_retry_count_reads_header():
    properties = SimpleNamespace(headers={"x-retry-count": 2})
    assert _extract_retry_count(properties) == 2


def test_handle_delivery_retries_failed_task(monkeypatch):
    monkeypatch.setattr(settings.worker, "requeue_on_failure", False)
    monkeypatch.setattr(settings.worker, "max_retries", 3)
    monkeypatch.setattr(settings.worker, "retry_delay_ms", 1000)
    monkeypatch.setattr(settings.worker, "max_retry_delay_ms", 5000)
    monkeypatch.setattr(settings.worker, "idempotency_enabled", False)
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr("app.worker.runner.dispatch_envelope", raise_envelope_failure)
    monkeypatch.setattr(
        "app.worker.runner.get_task_retry_policy",
        lambda task_name: TaskRetryPolicy(max_retries=3, base_delay_ms=1000, max_delay_ms=5000),
    )

    channel = FakeChannel()
    envelope = TaskEnvelope(task="user.registered", payload={"user_id": 1})
    body = envelope.model_dump_json().encode("utf-8")
    properties = SimpleNamespace(headers={"x-retry-count": 1})

    _handle_delivery(channel, make_delivery(), properties, body)

    assert channel.acked == [1]
    assert not channel.nacked
    assert len(channel.published) == 1
    assert channel.published[0]["routing_key"] == "app.default.retry"
    properties = cast(SimpleNamespace, channel.published[0]["properties"])
    assert properties.expiration == "2000"


def test_handle_delivery_dead_letters_after_max_retries(monkeypatch):
    monkeypatch.setattr(settings.worker, "requeue_on_failure", False)
    monkeypatch.setattr(settings.worker, "max_retries", 1)
    monkeypatch.setattr(settings.worker, "idempotency_enabled", False)
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr("app.worker.runner.dispatch_envelope", raise_envelope_failure)
    monkeypatch.setattr(
        "app.worker.runner.get_task_retry_policy",
        lambda task_name: TaskRetryPolicy(max_retries=1, base_delay_ms=1000, max_delay_ms=5000),
    )

    channel = FakeChannel()
    envelope = TaskEnvelope(task="user.registered", payload={"user_id": 1})
    body = envelope.model_dump_json().encode("utf-8")
    properties = SimpleNamespace(headers={"x-retry-count": 1})

    _handle_delivery(channel, make_delivery(), properties, body)

    assert channel.acked == [1]
    assert not channel.nacked
    assert len(channel.published) == 1
    assert channel.published[0]["routing_key"] == "app.default.dlq"


def test_handle_delivery_succeeds_and_acks(monkeypatch):
    monkeypatch.setattr("app.worker.runner.dispatch_envelope", lambda envelope: None)
    monkeypatch.setattr(settings.worker, "idempotency_enabled", False)
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")

    channel = FakeChannel()
    envelope = TaskEnvelope(task="user.registered", payload={"user_id": 1})
    body = envelope.model_dump_json().encode("utf-8")
    properties = SimpleNamespace(headers={})

    _handle_delivery(channel, make_delivery(), properties, body)

    assert channel.acked == [1]
    assert not channel.nacked
    assert channel.published == []


def test_handle_delivery_skips_completed_duplicate(monkeypatch):
    backend = SimpleNamespace(
        is_completed=lambda task_id: True,
        start=lambda task_id: False,
        complete=lambda task_id: None,
        release=lambda task_id: None,
    )
    monkeypatch.setattr(settings.worker, "idempotency_enabled", True)
    monkeypatch.setattr("app.worker.runner.worker_idempotency_backend", lambda: backend)
    monkeypatch.setattr("app.worker.runner.dispatch_envelope", lambda envelope: None)
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")

    channel = FakeChannel()
    envelope = TaskEnvelope(task="user.registered", payload={"user_id": 1})
    body = envelope.model_dump_json().encode("utf-8")
    properties = SimpleNamespace(headers={})

    _handle_delivery(channel, make_delivery(), properties, body)

    assert channel.acked == [1]
    assert channel.published == []


def test_handle_delivery_invalid_payload_retries(monkeypatch):
    monkeypatch.setattr(settings.worker, "requeue_on_failure", False)
    monkeypatch.setattr(settings.worker, "idempotency_enabled", False)
    monkeypatch.setattr(settings.worker, "retry_queue_name", "app.default.retry")
    monkeypatch.setattr(settings.worker, "dead_letter_queue_name", "app.default.dlq")
    monkeypatch.setattr(settings.worker, "queue_name", "app.default")
    monkeypatch.setattr(
        "app.worker.runner.get_task_retry_policy",
        lambda task_name: TaskRetryPolicy(max_retries=3, base_delay_ms=1000, max_delay_ms=5000),
    )

    channel = FakeChannel()
    envelope = TaskEnvelope(
        task="email.send_password_reset",
        payload={"user_id": 1, "email": "a@example.com"},
    )
    body = envelope.model_dump_json().encode("utf-8")
    properties = SimpleNamespace(headers={"x-retry-count": 0})

    _handle_delivery(channel, make_delivery(), properties, body)

    assert channel.acked == [1]
    assert channel.published[0]["routing_key"] == "app.default.retry"
