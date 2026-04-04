import json
import smtplib
from typing import Any
from urllib.error import URLError

import pytest

from app.core.config import settings
from app.providers.email import SendGridEmailProvider, SESEmailProvider, SMTPEmailProvider
from app.providers.webhook import HTTPWebhookProvider, SlackWebhookProvider


class FakeSMTP:
    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in: tuple[str, str] | None = None
        self.messages: list[object] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username: str, password: str):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.messages.append(message)


class FakeHTTPResponse:
    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSESClient:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def send_email(self, **kwargs):
        self.calls.append(kwargs)

    def send_templated_email(self, **kwargs):
        self.calls.append(kwargs)


class FakeSession:
    def __init__(self, client):
        self._client = client
        self.calls: list[tuple[str, dict[str, object]]] = []

    def client(self, service_name: str, **kwargs):
        self.calls.append((service_name, kwargs))
        return self._client


def test_smtp_email_provider_sends_message(monkeypatch):
    fake_smtp = FakeSMTP("smtp.example.com", 587, 10)

    monkeypatch.setattr(settings.email, "host", "smtp.example.com")
    monkeypatch.setattr(settings.email, "port", 587)
    monkeypatch.setattr(settings.email, "username", "smtp-user")
    monkeypatch.setattr(settings.email, "password", "smtp-pass")
    monkeypatch.setattr(settings.email, "use_tls", True)
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr("app.providers.email.smtplib.SMTP", lambda host, port, timeout: fake_smtp)

    SMTPEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert fake_smtp.started_tls is True
    assert fake_smtp.logged_in == ("smtp-user", "smtp-pass")
    assert len(fake_smtp.messages) == 1


def test_http_webhook_provider_sends_request(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.webhook, "user_registered_url", "https://example.com/webhook")
    monkeypatch.setattr(settings.webhook, "timeout_seconds", 5.0)
    monkeypatch.setattr(settings.webhook, "auth_header_name", "X-Webhook-Token")
    monkeypatch.setattr(settings.webhook, "auth_header_value", "secret-token")
    monkeypatch.setattr(settings.webhook, "allowed_hosts", ["example.com"])
    monkeypatch.setattr(settings.webhook, "allow_private_targets", False)
    monkeypatch.setattr(settings.webhook, "require_https", True)
    monkeypatch.setattr("app.providers.webhook.request.urlopen", fake_urlopen)

    HTTPWebhookProvider().send_user_registered_webhook(
        user_id=1,
        username="alice",
        email="user@example.com",
    )

    assert captured["url"] == "https://example.com/webhook"
    assert captured["timeout"] == 5.0
    assert captured["body"] is not None


def test_http_webhook_provider_blocks_non_allowlisted_hosts(monkeypatch):
    monkeypatch.setattr(settings.webhook, "user_registered_url", "https://evil.example.net/webhook")
    monkeypatch.setattr(settings.webhook, "allowed_hosts", ["hooks.example.com"])
    monkeypatch.setattr(settings.webhook, "allow_private_targets", False)
    monkeypatch.setattr(settings.webhook, "require_https", True)

    with pytest.raises(RuntimeError, match="WEBHOOK__ALLOWED_HOSTS"):
        HTTPWebhookProvider().send_user_registered_webhook(
            user_id=1,
            username="alice",
            email="user@example.com",
        )


def test_http_webhook_provider_blocks_private_targets(monkeypatch):
    monkeypatch.setattr(settings.webhook, "user_registered_url", "https://127.0.0.1/webhook")
    monkeypatch.setattr(settings.webhook, "allowed_hosts", [])
    monkeypatch.setattr(settings.webhook, "allow_private_targets", False)
    monkeypatch.setattr(settings.webhook, "require_https", True)

    with pytest.raises(RuntimeError, match="not allowed"):
        HTTPWebhookProvider().send_user_registered_webhook(
            user_id=1,
            username="alice",
            email="user@example.com",
        )


def test_sendgrid_email_provider_sends_request(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.email, "sendgrid_api_key", "sg-key")
    monkeypatch.setattr(settings.email, "sendgrid_api_base_url", "https://api.sendgrid.com/v3/mail/send")
    monkeypatch.setattr(settings.email, "sendgrid_timeout_seconds", 12.5)
    monkeypatch.setattr(settings.email, "sendgrid_categories", ["welcome", "signup"])
    monkeypatch.setattr(
        settings.email,
        "sendgrid_custom_args",
        {"tenant": "acme", "flow": "signup"},
    )
    monkeypatch.setattr(settings.email, "sendgrid_welcome_template_id", "d-template-123")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr("app.providers.email.request.urlopen", fake_urlopen)

    SendGridEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert captured["url"] == "https://api.sendgrid.com/v3/mail/send"
    assert captured["timeout"] == 12.5
    assert captured["body"] is not None
    payload = json.loads(captured["body"].decode("utf-8"))
    assert payload["categories"] == ["welcome", "signup"]
    assert payload["template_id"] == "d-template-123"
    assert payload["personalizations"][0]["custom_args"] == {"tenant": "acme", "flow": "signup"}
    assert payload["personalizations"][0]["dynamic_template_data"]["username"] == "alice"


def test_sendgrid_password_reset_uses_template_data(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.email, "sendgrid_api_key", "sg-key")
    monkeypatch.setattr(settings.email, "sendgrid_timeout_seconds", 10.0)
    monkeypatch.setattr(settings.email, "sendgrid_password_reset_template_id", "d-reset-123")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr("app.providers.email.request.urlopen", fake_urlopen)

    SendGridEmailProvider().send_password_reset_email(
        user_id=2,
        email="user@example.com",
        username="alice",
        reset_url="https://example.com/reset/token",
    )

    payload = json.loads(captured["body"].decode("utf-8"))
    assert payload["template_id"] == "d-reset-123"
    assert payload["personalizations"][0]["dynamic_template_data"]["reset_url"] == (
        "https://example.com/reset/token"
    )


def test_ses_email_provider_sends_message(monkeypatch):
    fake_client = FakeSESClient()

    monkeypatch.setattr(settings.email, "ses_region", "ap-southeast-1")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr(settings.email, "ses_configuration_set", "welcome-mails")
    monkeypatch.setattr(settings.email, "ses_welcome_template_name", "welcome-template")
    monkeypatch.setattr("boto3.client", lambda service_name, region_name: fake_client)

    SESEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert len(fake_client.calls) == 1
    assert fake_client.calls[0]["Source"] == "no-reply@example.com"
    assert fake_client.calls[0]["Template"] == "welcome-template"


def test_ses_verification_email_uses_template(monkeypatch):
    fake_client = FakeSESClient()

    monkeypatch.setattr(settings.email, "ses_region", "ap-southeast-1")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr(settings.email, "ses_verification_template_name", "verify-template")
    monkeypatch.setattr("boto3.client", lambda service_name, region_name: fake_client)

    SESEmailProvider().send_verification_email(
        user_id=3,
        email="user@example.com",
        username="alice",
        verification_url="https://example.com/verify/token",
    )

    assert fake_client.calls[0]["Template"] == "verify-template"
    template_data = fake_client.calls[0]["TemplateData"]
    assert isinstance(template_data, str)
    assert "verification_url" in template_data


def test_ses_email_provider_uses_profile_session(monkeypatch):
    fake_client = FakeSESClient()
    fake_session = FakeSession(fake_client)

    monkeypatch.setattr(settings.email, "ses_region", "us-east-1")
    monkeypatch.setattr(settings.email, "ses_profile_name", "platform-prod")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr("boto3.Session", lambda profile_name: fake_session)

    SESEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert fake_session.calls == [("ses", {"region_name": "us-east-1"})]
    assert len(fake_client.calls) == 1


def test_ses_email_provider_passes_explicit_credentials(monkeypatch):
    fake_client = FakeSESClient()
    captured: dict[str, Any] = {}

    def fake_boto3_client(service_name: str, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs
        return fake_client

    monkeypatch.setattr(settings.email, "ses_region", "ap-southeast-1")
    monkeypatch.setattr(settings.email, "ses_profile_name", None)
    monkeypatch.setattr(settings.email, "ses_access_key_id", "access-key")
    monkeypatch.setattr(settings.email, "ses_secret_access_key", "secret-key")
    monkeypatch.setattr(settings.email, "ses_session_token", "session-token")
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr("boto3.client", fake_boto3_client)

    SESEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert captured["service_name"] == "ses"
    kwargs = captured["kwargs"]
    assert kwargs["region_name"] == "ap-southeast-1"
    assert kwargs["aws_access_key_id"] == "access-key"
    assert kwargs["aws_secret_access_key"] == "secret-key"
    assert kwargs["aws_session_token"] == "session-token"


def test_slack_webhook_provider_sends_request(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.webhook, "slack_webhook_url", "https://hooks.slack.test/services/abc")
    monkeypatch.setattr(settings.webhook, "timeout_seconds", 5.0)
    monkeypatch.setattr(settings.webhook, "slack_channel", "#ops")
    monkeypatch.setattr(settings.webhook, "slack_username", "fastapi-bot")
    monkeypatch.setattr(settings.webhook, "slack_icon_emoji", ":rocket:")
    monkeypatch.setattr(settings.webhook, "allowed_hosts", ["hooks.slack.test"])
    monkeypatch.setattr(settings.webhook, "require_https", True)
    monkeypatch.setattr(
        settings.webhook,
        "slack_route_urls",
        {"user_registered": "https://hooks.slack.test/services/routed"},
    )
    monkeypatch.setattr("app.providers.webhook.request.urlopen", fake_urlopen)

    SlackWebhookProvider().send_user_registered_webhook(
        user_id=1,
        username="alice",
        email="user@example.com",
    )

    assert captured["url"] == "https://hooks.slack.test/services/routed"
    assert captured["timeout"] == 5.0
    assert captured["body"] is not None
    payload = json.loads(captured["body"].decode("utf-8"))
    assert payload["blocks"][0]["type"] == "header"
    assert payload["channel"] == "#ops"


def test_slack_worker_failure_alert_uses_route_mapping(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data
        captured["timeout"] = timeout
        return FakeHTTPResponse()

    monkeypatch.setattr(
        settings.webhook,
        "slack_route_urls",
        {"worker_failure": "https://hooks.slack.test/services/worker-failure"},
    )
    monkeypatch.setattr(settings.webhook, "slack_webhook_url", "https://hooks.slack.test/services/default")
    monkeypatch.setattr(settings.webhook, "timeout_seconds", 5.0)
    monkeypatch.setattr(settings.webhook, "allowed_hosts", ["hooks.slack.test"])
    monkeypatch.setattr(settings.webhook, "require_https", True)
    monkeypatch.setattr("app.providers.webhook.request.urlopen", fake_urlopen)

    SlackWebhookProvider().send_worker_failure_alert(
        task_name="email.send_verification",
        task_id="task-123",
        error_message="SMTP timeout",
    )

    payload = json.loads(captured["body"].decode("utf-8"))
    assert captured["url"] == "https://hooks.slack.test/services/worker-failure"
    assert payload["blocks"][0]["text"]["text"] == "Worker Failure Alert"
    assert "SMTP timeout" in payload["blocks"][2]["text"]["text"]


def test_sendgrid_email_provider_retries_retryable_http_errors(monkeypatch):
    attempts = {"count": 0}

    def fake_urlopen(req, timeout):
        del req, timeout
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise URLError("temporary network issue")
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.email, "sendgrid_api_key", "sg-key")
    monkeypatch.setattr(settings.email, "sendgrid_timeout_seconds", 12.5)
    monkeypatch.setattr(settings.external, "max_attempts", 3)
    monkeypatch.setattr("app.providers.email.request.urlopen", fake_urlopen)
    monkeypatch.setattr("app.core.resilience.sleep", lambda seconds: None)

    SendGridEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert attempts["count"] == 3


def test_sendgrid_event_specific_retry_policy_overrides_provider_policy(monkeypatch):
    attempts = {"count": 0}

    def fake_urlopen(req, timeout):
        del req, timeout
        attempts["count"] += 1
        if attempts["count"] < 4:
            raise URLError("temporary network issue")
        return FakeHTTPResponse()

    monkeypatch.setattr(settings.email, "sendgrid_api_key", "sg-key")
    monkeypatch.setattr(settings.email, "sendgrid_timeout_seconds", 12.5)
    monkeypatch.setattr(settings.external_policies.sendgrid, "max_attempts", 2)
    monkeypatch.setattr(
        settings.external_event_policies,
        "email_send_welcome",
        settings.external_policies.sendgrid.model_copy(
            update={
                "max_attempts": 4,
                "backoff_seconds": 0.01,
                "max_backoff_seconds": 0.01,
            }
        ),
    )
    monkeypatch.setattr("app.providers.email.request.urlopen", fake_urlopen)
    monkeypatch.setattr("app.core.resilience.sleep", lambda seconds: None)

    SendGridEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert attempts["count"] == 4


def test_smtp_email_provider_retries_smtp_errors(monkeypatch):
    attempts = {"count": 0}

    class FlakySMTP(FakeSMTP):
        def send_message(self, message):
            del message
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise smtplib.SMTPServerDisconnected("temporary disconnect")

    monkeypatch.setattr(settings.email, "host", "smtp.example.com")
    monkeypatch.setattr(settings.email, "port", 587)
    monkeypatch.setattr(settings.email, "use_tls", False)
    monkeypatch.setattr(settings.email, "from_email", "no-reply@example.com")
    monkeypatch.setattr(settings.external, "timeout_seconds", 10.0)
    monkeypatch.setattr(settings.external, "max_attempts", 3)
    monkeypatch.setattr(
        "app.providers.email.smtplib.SMTP",
        lambda host, port, timeout: FlakySMTP(host, port, timeout),
    )
    monkeypatch.setattr("app.core.resilience.sleep", lambda seconds: None)

    SMTPEmailProvider().send_welcome_email(
        user_id=1,
        email="user@example.com",
        username="alice",
    )

    assert attempts["count"] == 3
