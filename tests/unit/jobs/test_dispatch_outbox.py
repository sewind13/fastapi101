from app.db.models.outbox_event import OutboxEvent
from app.jobs.dispatch_outbox import dispatch_outbox_batch
from tests.unit.repositories.conftest import session as session


def test_dispatch_outbox_batch_marks_events_published(session, monkeypatch):
    event = OutboxEvent(
        task_id="dispatch-1",
        task_name="user.registered",
        payload={"user_id": 1},
        source="test",
    )
    session.add(event)
    session.commit()

    monkeypatch.setattr("app.jobs.dispatch_outbox.SessionLocal", lambda: session)
    monkeypatch.setattr("app.jobs.dispatch_outbox.publish_envelope", lambda envelope: True)

    published, retried, failed = dispatch_outbox_batch(limit=10)

    assert (published, retried, failed) == (1, 0, 0)
    refreshed = session.get(OutboxEvent, event.id)
    assert refreshed is not None
    assert refreshed.status == "published"


def test_dispatch_outbox_batch_reschedules_failed_events(session, monkeypatch):
    event = OutboxEvent(
        task_id="dispatch-2",
        task_name="email.send_welcome",
        payload={"user_id": 1},
        source="test",
    )
    session.add(event)
    session.commit()

    monkeypatch.setattr("app.jobs.dispatch_outbox.SessionLocal", lambda: session)
    monkeypatch.setattr(
        "app.jobs.dispatch_outbox.publish_envelope",
        lambda envelope: (_ for _ in ()).throw(RuntimeError("broker down")),
    )

    published, retried, failed = dispatch_outbox_batch(limit=10)

    assert (published, retried, failed) == (0, 1, 0)
    refreshed = session.get(OutboxEvent, event.id)
    assert refreshed is not None
    assert refreshed.status == "pending"
    assert refreshed.attempts == 1
    assert refreshed.last_error == "broker down"
