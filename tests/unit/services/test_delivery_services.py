from app.services.email_service import send_welcome_email
from app.services.webhook_service import send_user_registered_webhook


class FakeEmailProvider:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None:
        self.calls.append({"user_id": user_id, "email": email, "username": username})


class FakeWebhookProvider:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def send_user_registered_webhook(
        self,
        *,
        user_id: object,
        username: object,
        email: object,
    ) -> None:
        self.calls.append({"user_id": user_id, "username": username, "email": email})


def test_send_welcome_email_dry_run(monkeypatch):
    provider = FakeEmailProvider()
    monkeypatch.setattr("app.services.email_service.get_email_provider", lambda: provider)

    send_welcome_email(user_id=1, email="user@example.com", username="alice")

    assert provider.calls[0]["email"] == "user@example.com"

def test_send_user_registered_webhook_delegates_to_provider(monkeypatch):
    provider = FakeWebhookProvider()
    monkeypatch.setattr("app.services.webhook_service.get_webhook_provider", lambda: provider)

    send_user_registered_webhook(user_id=1, username="alice", email="user@example.com")

    assert provider.calls[0]["username"] == "alice"
