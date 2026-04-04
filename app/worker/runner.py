import json

import pika  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.metrics import observe_worker_event, observe_worker_queue_depth
from app.worker.idempotency import worker_idempotency_backend
from app.worker.publisher import ensure_worker_topology
from app.worker.schemas import TaskEnvelope
from app.worker.tasks import dispatch_envelope, get_task_retry_policy


def _extract_retry_count(properties: pika.BasicProperties) -> int:
    headers = properties.headers or {}
    retry_count = headers.get("x-retry-count", 0)
    try:
        return int(retry_count)
    except (TypeError, ValueError):
        return 0


def _publish_retry(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    *,
    envelope: TaskEnvelope,
    retry_count: int,
) -> None:
    retry_policy = get_task_retry_policy(envelope.task)
    retry_delay_ms = min(
        retry_policy.base_delay_ms * (2 ** max(retry_count - 1, 0)),
        retry_policy.max_delay_ms,
    )
    channel.basic_publish(
        exchange="",
        routing_key=settings.worker.retry_queue_name,
        body=envelope.model_dump_json().encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            headers={"x-retry-count": retry_count},
            expiration=str(retry_delay_ms),
        ),
    )


def _publish_dead_letter(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    *,
    envelope: TaskEnvelope,
    retry_count: int,
) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=settings.worker.dead_letter_queue_name,
        body=envelope.model_dump_json().encode("utf-8"),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            headers={"x-retry-count": retry_count},
        ),
    )


def _observe_queue_depths(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    for queue_name in (
        settings.worker.queue_name,
        settings.worker.retry_queue_name,
        settings.worker.dead_letter_queue_name,
    ):
        result = channel.queue_declare(queue=queue_name, passive=True)
        observe_worker_queue_depth(
            queue_name=queue_name,
            depth=int(getattr(result.method, "message_count", 0)),
        )


def _handle_delivery(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.BasicProperties,
    body: bytes,
) -> None:
    retry_count = _extract_retry_count(properties)
    envelope: TaskEnvelope | None = None
    idempotency = worker_idempotency_backend()
    try:
        envelope = TaskEnvelope.model_validate(json.loads(body.decode("utf-8")))
        task_id = envelope.metadata.task_id
        if settings.worker.idempotency_enabled:
            if idempotency.is_completed(task_id):
                observe_worker_event(task_name=envelope.task, outcome="skipped_duplicate")
                channel.basic_ack(delivery_tag=method.delivery_tag)
                _observe_queue_depths(channel)
                return
            if not idempotency.start(task_id):
                observe_worker_event(task_name=envelope.task, outcome="skipped_duplicate")
                channel.basic_ack(delivery_tag=method.delivery_tag)
                _observe_queue_depths(channel)
                return
        observe_worker_event(task_name=envelope.task, outcome="started")
        dispatch_envelope(envelope)
        if settings.worker.idempotency_enabled:
            idempotency.complete(task_id)
        observe_worker_event(task_name=envelope.task, outcome="succeeded")
        channel.basic_ack(delivery_tag=method.delivery_tag)
        _observe_queue_depths(channel)
    except Exception:
        task_name = "unknown"
        try:
            envelope = TaskEnvelope.model_validate(json.loads(body.decode("utf-8")))
            task_name = envelope.task
        except Exception:
            pass

        observe_worker_event(task_name=task_name, outcome="failed")
        logger.exception(
            "background task failed",
            extra={
                "event_type": "worker",
                "task_name": task_name,
                "retry_count": retry_count,
            },
        )
        if settings.worker.requeue_on_failure:
            if envelope is not None and settings.worker.idempotency_enabled:
                idempotency.release(envelope.metadata.task_id)
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )
            return

        retry_policy = get_task_retry_policy(task_name)
        if envelope is not None and retry_count < retry_policy.max_retries:
            if settings.worker.idempotency_enabled:
                idempotency.release(envelope.metadata.task_id)
            _publish_retry(channel, envelope=envelope, retry_count=retry_count + 1)
            observe_worker_event(task_name=task_name, outcome="retried")
        elif envelope is not None:
            if settings.worker.idempotency_enabled:
                idempotency.release(envelope.metadata.task_id)
            _publish_dead_letter(channel, envelope=envelope, retry_count=retry_count)
            observe_worker_event(task_name=task_name, outcome="dead_lettered")

        channel.basic_ack(delivery_tag=method.delivery_tag)
        _observe_queue_depths(channel)


def main() -> int:
    configure_logging()

    if not settings.worker.enabled:
        logger.info(
            "background worker is disabled",
            extra={"event_type": "worker"},
        )
        return 0

    if not settings.worker.broker_url:
        logger.error(
            "background worker broker URL is not configured",
            extra={"event_type": "worker"},
        )
        return 1

    logger.info(
        "starting background worker",
        extra={
            "event_type": "worker",
            "queue_name": settings.worker.queue_name,
        },
    )
    parameters = pika.URLParameters(settings.worker.broker_url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    ensure_worker_topology(channel)
    _observe_queue_depths(channel)
    channel.basic_qos(prefetch_count=settings.worker.prefetch_count)
    channel.basic_consume(
        queue=settings.worker.queue_name,
        on_message_callback=_handle_delivery,
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info(
            "background worker stopped",
            extra={"event_type": "worker"},
        )
    finally:
        if connection.is_open:
            connection.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
