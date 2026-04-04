from app.db.models.outbox_event import OutboxEvent
from app.db.repositories.outbox_event import (
    list_pending_outbox_events,
    mark_outbox_event_published,
)


def test_list_pending_outbox_events_returns_pending_rows(session):
    event = OutboxEvent(
        task_id="task-1",
        task_name="user.registered",
        payload={"user_id": 1},
        source="test",
    )
    session.add(event)
    session.commit()

    events = list_pending_outbox_events(session, limit=10)

    assert len(events) == 1
    assert events[0].task_id == "task-1"


def test_mark_outbox_event_published_updates_status(session):
    event = OutboxEvent(
        task_id="task-2",
        task_name="email.send_welcome",
        payload={"user_id": 1},
        source="test",
    )
    session.add(event)
    session.commit()

    mark_outbox_event_published(session, event)
    session.commit()

    refreshed = session.get(OutboxEvent, event.id)
    assert refreshed is not None
    assert refreshed.status == "published"
    assert refreshed.published_at is not None
