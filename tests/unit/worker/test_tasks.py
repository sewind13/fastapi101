import pytest
from pydantic import ValidationError

from app.worker.schemas import TaskEnvelope
from app.worker.tasks import dispatch_envelope, dispatch_task


def test_dispatch_task_rejects_unknown_task():
    with pytest.raises(ValueError, match="Unknown worker task"):
        dispatch_task("unknown.task", {})


def test_email_task_calls_email_service(monkeypatch):
    called = {}

    def fake_send_welcome_email(*, user_id, email, username):
        called["payload"] = {
            "user_id": user_id,
            "email": email,
            "username": username,
        }

    monkeypatch.setattr("app.worker.tasks.send_welcome_email", fake_send_welcome_email)

    dispatch_task(
        "email.send_welcome",
        {"user_id": 1, "email": "user@example.com", "username": "alice"},
    )

    assert called["payload"]["user_id"] == 1
    assert called["payload"]["email"] == "user@example.com"


def test_webhook_task_calls_webhook_service(monkeypatch):
    called = {}

    def fake_send_user_registered_webhook(*, user_id, username, email):
        called["payload"] = {
            "user_id": user_id,
            "username": username,
            "email": email,
        }

    monkeypatch.setattr(
        "app.worker.tasks.send_user_registered_webhook",
        fake_send_user_registered_webhook,
    )

    dispatch_task(
        "webhook.user_registered",
        {"user_id": 2, "email": "webhook@example.com", "username": "bob"},
    )

    assert called["payload"]["user_id"] == 2
    assert called["payload"]["username"] == "bob"


def test_password_reset_email_task_calls_email_service(monkeypatch):
    called = {}

    def fake_send_password_reset_email(*, user_id, email, username, reset_url):
        called["payload"] = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "reset_url": reset_url,
        }

    monkeypatch.setattr(
        "app.worker.tasks.send_password_reset_email",
        fake_send_password_reset_email,
    )

    dispatch_task(
        "email.send_password_reset",
        {
            "user_id": 3,
            "email": "reset@example.com",
            "username": "carol",
            "reset_url": "https://example.com/reset/token",
        },
    )

    assert called["payload"]["reset_url"] == "https://example.com/reset/token"


def test_verification_email_task_calls_email_service(monkeypatch):
    called = {}

    def fake_send_verification_email(*, user_id, email, username, verification_url):
        called["payload"] = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "verification_url": verification_url,
        }

    monkeypatch.setattr("app.worker.tasks.send_verification_email", fake_send_verification_email)

    dispatch_task(
        "email.send_verification",
        {
            "user_id": 4,
            "email": "verify@example.com",
            "username": "dave",
            "verification_url": "https://example.com/verify/token",
        },
    )

    assert called["payload"]["verification_url"] == "https://example.com/verify/token"


def test_worker_failure_alert_task_calls_webhook_service(monkeypatch):
    called = {}

    def fake_send_worker_failure_alert(*, task_name, task_id, error_message):
        called["payload"] = {
            "task_name": task_name,
            "task_id": task_id,
            "error_message": error_message,
        }

    monkeypatch.setattr(
        "app.worker.tasks.send_worker_failure_alert",
        fake_send_worker_failure_alert,
    )

    dispatch_task(
        "webhook.worker_failure_alert",
        {
            "task_name": "email.send_verification",
            "task_id": "task-456",
            "error_message": "SMTP timeout",
        },
    )

    assert called["payload"]["task_id"] == "task-456"


def test_dispatch_task_validates_password_reset_payload():
    with pytest.raises(ValidationError):
        dispatch_task(
            "email.send_password_reset",
            {
                "user_id": 3,
                "email": "reset@example.com",
                "username": "carol",
            },
        )


def test_dispatch_envelope_validates_and_calls_handler(monkeypatch):
    called = {}

    def fake_send_verification_email(*, user_id, email, username, verification_url):
        called["payload"] = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "verification_url": verification_url,
        }

    monkeypatch.setattr("app.worker.tasks.send_verification_email", fake_send_verification_email)

    dispatch_envelope(
        TaskEnvelope(
            task="email.send_verification",
            payload={
                "user_id": 4,
                "email": "verify@example.com",
                "username": "dave",
                "verification_url": "https://example.com/verify/token",
            },
        )
    )

    assert called["payload"]["verification_url"] == "https://example.com/verify/token"
