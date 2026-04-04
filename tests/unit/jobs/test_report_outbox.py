from app.db.models.outbox_event import OutboxEvent
from app.jobs.report_outbox import report_outbox
from tests.unit.repositories.conftest import session as session


def test_report_outbox_returns_status_counts(session, monkeypatch):
    session.add(
        OutboxEvent(
            task_id="outbox-1",
            task_name="user.registered",
            payload={"user_id": 1},
            source="test",
            status="pending",
        )
    )
    session.add(
        OutboxEvent(
            task_id="outbox-2",
            task_name="email.send_welcome",
            payload={"user_id": 1},
            source="test",
            status="failed",
        )
    )
    session.commit()

    from app.jobs import report_outbox as report_outbox_module

    monkeypatch.setattr(report_outbox_module, "SessionLocal", lambda: session)

    summary = report_outbox()

    assert summary["pending"] == 1
    assert summary["failed"] == 1
    assert summary["published"] == 0
    assert summary["total"] == 2
