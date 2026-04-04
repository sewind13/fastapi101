from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.outbox_event import OutboxEvent
from tests.conftest import build_token_headers, create_test_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_outbox_summary_requires_ops_admin_flag(client, session):
    user = create_test_user(session, username="plainuser", email="plain@example.com")
    assert user.id is not None

    response = await client.get(
        "/api/v1/ops/outbox/summary",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_outbox_summary_returns_data_for_ops_admin(client, session):
    admin = create_test_user(
        session,
        username="opsadmin",
        email="admin@example.com",
        role="ops_admin",
    )
    assert admin.id is not None

    response = await client.get(
        "/api/v1/ops/outbox/summary",
        headers=build_token_headers(admin.id, admin.username),
    )

    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "failed" in data
    assert "published" in data
    assert "total" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_outbox_events_returns_list(client, session):
    admin = create_test_user(
        session,
        username="opsadmin2",
        email="admin2@example.com",
        role="ops_admin",
    )
    assert admin.id is not None

    response = await client.get(
        "/api/v1/ops/outbox/events?limit=10",
        headers=build_token_headers(admin.id, admin.username),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_outbox_events_supports_filters(client, session):
    admin = create_test_user(
        session,
        username="opsadmin3",
        email="admin3@example.com",
        role="ops_admin",
    )
    assert admin.id is not None

    session.add_all(
        [
            OutboxEvent(
                task_id="task-email-1",
                task_name="email.send_welcome",
                status="pending",
                payload={"email": "a@example.com"},
                available_at=datetime.now(UTC),
            ),
            OutboxEvent(
                task_id="task-webhook-1",
                task_name="webhook.user_registered",
                status="failed",
                payload={"email": "b@example.com"},
                available_at=datetime.now(UTC),
            ),
        ]
    )
    session.commit()

    response = await client.get(
        "/api/v1/ops/outbox/events?status=failed&task_name=webhook&task_id=webhook-1",
        headers=build_token_headers(admin.id, admin.username),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_name"] == "webhook.user_registered"
    assert data[0]["status"] == "failed"
    assert data[0]["task_id"] == "task-webhook-1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_user_auth_state_returns_lockout_details(client, session):
    admin = create_test_user(
        session,
        username="opsadmin4",
        email="admin4@example.com",
        role="ops_admin",
    )
    assert admin.id is not None
    locked_user = create_test_user(
        session,
        username="lockeduser",
        email="locked@example.com",
    )
    assert locked_user.id is not None
    locked_user.failed_login_attempts = 4
    locked_user.locked_until = datetime.now(UTC) + timedelta(minutes=5)
    session.add(locked_user)
    session.commit()

    response = await client.get(
        f"/api/v1/ops/users/{locked_user.id}/auth-state",
        headers=build_token_headers(admin.id, admin.username),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "lockeduser"
    assert data["failed_login_attempts"] == 4
    assert data["locked_until"] is not None
    assert data["is_locked"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_can_unlock_user_account(client, session):
    admin = create_test_user(
        session,
        username="opsadmin5",
        email="admin5@example.com",
        role="ops_admin",
    )
    assert admin.id is not None
    locked_user = create_test_user(
        session,
        username="lockeduser2",
        email="locked2@example.com",
    )
    assert locked_user.id is not None
    locked_user.failed_login_attempts = 5
    locked_user.locked_until = datetime.now(UTC) + timedelta(minutes=5)
    session.add(locked_user)
    session.commit()

    response = await client.post(
        f"/api/v1/ops/users/{locked_user.id}/unlock",
        headers=build_token_headers(admin.id, admin.username),
    )

    session.refresh(locked_user)

    assert response.status_code == 200
    assert response.json()["message"] == "User account lockout cleared."
    assert locked_user.failed_login_attempts == 0
    assert locked_user.locked_until is None
