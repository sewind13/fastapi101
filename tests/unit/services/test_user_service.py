from sqlmodel import select

from app.db.models.outbox_event import OutboxEvent
from app.schemas.user import UserCreate
from app.services.user_service import create_user


def test_create_user_persists_outbox_events(session):
    result = create_user(
        session=session,
        user_in=UserCreate(
            username="outboxuser",
            email="outbox@example.com",
            password="strongpassword123",
        ),
        request_id="req-outbox",
    )

    assert result.ok is True
    assert result.value is not None

    events = session.exec(select(OutboxEvent)).all()
    assert len(events) == 4
    assert {event.task_name for event in events} == {
        "user.registered",
        "email.send_welcome",
        "email.send_verification",
        "webhook.user_registered",
    }
    assert all(event.payload["user_id"] == result.value.id for event in events)
    assert result.value.account_id is not None
