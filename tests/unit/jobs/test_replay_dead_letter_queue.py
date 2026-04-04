from types import SimpleNamespace
from typing import cast

from app.jobs.replay_dead_letter_queue import replay_dead_letter_queue


class FakeReplayChannel:
    def __init__(self):
        self.published: list[dict[str, object]] = []
        self.acked: list[int] = []
        self.declared: list[str] = []
        self.messages = [
            (
                SimpleNamespace(delivery_tag=1),
                SimpleNamespace(content_type="application/json", headers={"x-retry-count": 3}),
                b'{"task":"email.send_welcome","payload":{"user_id":1}}',
            )
        ]

    def queue_declare(
        self,
        *,
        queue: str,
        durable: bool = True,
        arguments=None,
        passive: bool = False,
    ):
        del durable, arguments, passive
        self.declared.append(queue)
        return SimpleNamespace(method=SimpleNamespace(message_count=0))

    def basic_get(self, *, queue: str, auto_ack: bool):
        del queue, auto_ack
        if self.messages:
            return self.messages.pop(0)
        return None, None, None

    def basic_publish(self, *, exchange: str, routing_key: str, body: bytes, properties):
        self.published.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "properties": properties,
            }
        )

    def basic_ack(self, *, delivery_tag: int):
        self.acked.append(delivery_tag)


class FakeReplayConnection:
    def __init__(self):
        self.channel_instance = FakeReplayChannel()
        self.closed = False

    def channel(self):
        return self.channel_instance

    def close(self):
        self.closed = True


def test_replay_dead_letter_queue_republishes_messages(monkeypatch):
    fake_connection = FakeReplayConnection()

    monkeypatch.setattr(
        "app.jobs.replay_dead_letter_queue.settings.worker.broker_url",
        "amqp://guest:guest@queue:5672/",
    )
    monkeypatch.setattr(
        "app.jobs.replay_dead_letter_queue.settings.worker.queue_name",
        "app.default",
    )
    monkeypatch.setattr(
        "app.jobs.replay_dead_letter_queue.settings.worker.dead_letter_queue_name",
        "app.default.dlq",
    )
    monkeypatch.setattr(
        "app.jobs.replay_dead_letter_queue.pika.URLParameters",
        lambda url: url,
    )
    monkeypatch.setattr(
        "app.jobs.replay_dead_letter_queue.pika.BlockingConnection",
        lambda parameters: fake_connection,
    )

    replayed = replay_dead_letter_queue(limit=10)

    assert replayed == 1
    assert fake_connection.channel_instance.acked == [1]
    assert fake_connection.channel_instance.published[0]["routing_key"] == "app.default"
    properties = cast(SimpleNamespace, fake_connection.channel_instance.published[0]["properties"])
    assert properties.headers == {}
    assert fake_connection.closed is True
