from typing import Any

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.worker.publisher import ensure_worker_topology

DEFAULT_REPLAY_LIMIT = 100
pika: Any = None


def _get_pika() -> Any:
    global pika
    if pika is None:
        import pika as pika_module  # type: ignore[import-untyped]

        pika = pika_module
    return pika


def replay_dead_letter_queue(*, limit: int = DEFAULT_REPLAY_LIMIT) -> int:
    if not settings.worker.broker_url:
        raise RuntimeError("WORKER__BROKER_URL is not configured.")

    pika_module = _get_pika()
    parameters = pika_module.URLParameters(settings.worker.broker_url)
    connection = pika_module.BlockingConnection(parameters)
    replayed = 0

    try:
        channel = connection.channel()
        ensure_worker_topology(channel)

        while replayed < limit:
            method, properties, body = channel.basic_get(
                queue=settings.worker.dead_letter_queue_name,
                auto_ack=False,
            )
            if method is None:
                break

            headers = dict(properties.headers or {})
            headers.pop("x-retry-count", None)

            channel.basic_publish(
                exchange="",
                routing_key=settings.worker.queue_name,
                body=body,
                properties=pika_module.BasicProperties(
                    content_type=properties.content_type or "application/json",
                    delivery_mode=2,
                    headers=headers,
                ),
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            replayed += 1

        logger.info(
            "dead-letter queue replay completed",
            extra={
                "event_type": "worker",
                "queue_name": settings.worker.dead_letter_queue_name,
                "replayed_count": replayed,
            },
        )
        return replayed
    finally:
        connection.close()


def main() -> int:
    configure_logging()
    replayed = replay_dead_letter_queue()
    return 0 if replayed >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
