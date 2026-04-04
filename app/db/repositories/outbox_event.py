from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.models.outbox_event import OutboxEvent
from app.db.repositories.exceptions import RepositoryError


def create_outbox_events(session: Session, events: list[OutboxEvent]) -> list[OutboxEvent]:
    try:
        session.add_all(events)
        return events
    except Exception as exc:
        raise RepositoryError("Failed to stage outbox events") from exc


def list_pending_outbox_events(session: Session, *, limit: int) -> list[OutboxEvent]:
    now = datetime.now(UTC)
    statement = (
        select(OutboxEvent)
        .where(OutboxEvent.status == "pending")
        .where(OutboxEvent.available_at <= now)
        .order_by("id")
        .limit(limit)
    )
    return list(session.exec(statement).all())


def mark_outbox_event_published(session: Session, event: OutboxEvent) -> None:
    event.status = "published"
    event.published_at = datetime.now(UTC)
    event.last_error = None
    session.add(event)


def mark_outbox_event_pending(
    session: Session,
    event: OutboxEvent,
    *,
    attempts: int,
    available_at: datetime,
    last_error: str,
) -> None:
    event.status = "pending"
    event.attempts = attempts
    event.available_at = available_at
    event.last_error = last_error[:500]
    session.add(event)


def mark_outbox_event_failed(session: Session, event: OutboxEvent, *, last_error: str) -> None:
    event.status = "failed"
    event.attempts += 1
    event.last_error = last_error[:500]
    session.add(event)


def count_outbox_events_by_status(session: Session, *, status: str) -> int:
    statement = select(OutboxEvent).where(OutboxEvent.status == status)
    return len(list(session.exec(statement).all()))
