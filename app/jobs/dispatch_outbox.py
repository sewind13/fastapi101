from datetime import UTC, datetime, timedelta
from time import sleep

from app.core.logging import configure_logging, logger
from app.core.metrics import observe_outbox_dispatch
from app.db.models.outbox_event import OutboxEvent
from app.db.repositories.outbox_event import (
    list_pending_outbox_events,
    mark_outbox_event_failed,
    mark_outbox_event_pending,
    mark_outbox_event_published,
)
from app.db.session import SessionLocal
from app.worker.publisher import publish_envelope
from app.worker.schemas import TaskEnvelope, TaskMetadata
from app.worker.tasks import get_task_retry_policy

DEFAULT_BATCH_SIZE = 100
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_MAX_ATTEMPTS = 20


def _build_envelope(event: OutboxEvent) -> TaskEnvelope:
    return TaskEnvelope(
        task=event.task_name,
        payload=event.payload,
        metadata=TaskMetadata(
            task_id=event.task_id,
            source=event.source,
        ),
    )


def dispatch_outbox_batch(*, limit: int = DEFAULT_BATCH_SIZE) -> tuple[int, int, int]:
    published = 0
    retried = 0
    failed = 0

    with SessionLocal() as session:
        events = list_pending_outbox_events(session, limit=limit)
        for event in events:
            try:
                ok = publish_envelope(envelope=_build_envelope(event))
                if not ok:
                    raise RuntimeError("Worker broker is not configured.")
                mark_outbox_event_published(session, event)
                published += 1
            except Exception as exc:
                next_attempt = event.attempts + 1
                retry_policy = get_task_retry_policy(event.task_name)
                if next_attempt >= min(retry_policy.max_retries + 1, DEFAULT_MAX_ATTEMPTS):
                    mark_outbox_event_failed(session, event, last_error=str(exc))
                    failed += 1
                else:
                    delay_ms = min(
                        retry_policy.base_delay_ms * (2 ** max(event.attempts, 0)),
                        retry_policy.max_delay_ms,
                    )
                    available_at = datetime.now(UTC) + timedelta(milliseconds=delay_ms)
                    mark_outbox_event_pending(
                        session,
                        event,
                        attempts=next_attempt,
                        available_at=available_at,
                        last_error=str(exc),
                    )
                    retried += 1
        session.commit()

    observe_outbox_dispatch(outcome="published", count=published)
    observe_outbox_dispatch(outcome="retried", count=retried)
    observe_outbox_dispatch(outcome="failed", count=failed)
    return published, retried, failed


def main(*, once: bool = False) -> int:
    configure_logging()
    while True:
        published, retried, failed = dispatch_outbox_batch()
        logger.info(
            "outbox dispatch cycle completed",
            extra={
                "event_type": "outbox",
                "published_count": published,
                "retried_count": retried,
                "failed_count": failed,
            },
        )
        if once:
            return 0
        sleep(DEFAULT_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
