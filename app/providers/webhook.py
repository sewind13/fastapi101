import json
from collections.abc import Callable
from ipaddress import ip_address
from typing import Protocol
from urllib import request
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import logger
from app.core.resilience import get_event_retry_policy, is_retryable_http_error, retry_call


class WebhookProvider(Protocol):
    def send_user_registered_webhook(
        self,
        *,
        user_id: object,
        username: object,
        email: object,
    ) -> None: ...

    def send_worker_failure_alert(
        self,
        *,
        task_name: object,
        task_id: object,
        error_message: object,
    ) -> None: ...


def format_slack_user_registered_message(
    *,
    user_id: object,
    username: object,
    email: object,
) -> dict[str, object]:
    return {
        "text": f"New user registered: {username} <{email}> (id={user_id})",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "New User Registration"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Username:*\n{username}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                    {"type": "mrkdwn", "text": f"*User ID:*\n{user_id}"},
                ],
            },
        ],
    }


SlackFormatter = Callable[..., dict[str, object]]

SLACK_FORMATTERS: dict[str, SlackFormatter] = {
    "user_registered": format_slack_user_registered_message,
}


def format_slack_worker_failure_message(
    *,
    task_name: object,
    task_id: object,
    error_message: object,
) -> dict[str, object]:
    return {
        "text": f"Worker task failed: {task_name} ({task_id})",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Worker Failure Alert"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Task:*\n{task_name}"},
                    {"type": "mrkdwn", "text": f"*Task ID:*\n{task_id}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error_message}```"},
            },
        ],
    }


SLACK_FORMATTERS["worker_failure"] = format_slack_worker_failure_message


class ConsoleWebhookProvider:
    def send_user_registered_webhook(
        self,
        *,
        user_id: object,
        username: object,
        email: object,
    ) -> None:
        self._log_skip(
            task_name="webhook.user_registered",
            user_id=user_id,
            username=username,
            email=email,
        )

    def send_worker_failure_alert(
        self,
        *,
        task_name: object,
        task_id: object,
        error_message: object,
    ) -> None:
        self._log_skip(
            task_name="webhook.worker_failure_alert",
            failed_task_name=task_name,
            failed_task_id=task_id,
            error_message=error_message,
        )

    def _log_skip(self, *, task_name: str, **extra: object) -> None:
        logger.info(
            "skipped webhook delivery",
            extra={
                "event_type": "webhook",
                "task_name": task_name,
                **extra,
            },
        )


class HTTPWebhookProvider:
    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        if parsed.scheme not in {"http", "https"}:
            raise RuntimeError("Webhook URL must use http or https.")

        if settings.webhook.require_https and parsed.scheme != "https":
            raise RuntimeError("Webhook URL must use https.")

        if not hostname:
            raise RuntimeError("Webhook URL must include a host.")

        if settings.webhook.allowed_hosts and hostname not in settings.webhook.allowed_hosts:
            raise RuntimeError("Webhook target host is not in WEBHOOK__ALLOWED_HOSTS.")

        if settings.webhook.allow_private_targets:
            return

        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
            raise RuntimeError("Webhook target host is not allowed.")

        try:
            parsed_ip = ip_address(hostname)
        except ValueError:
            return

        if (
            parsed_ip.is_private
            or parsed_ip.is_loopback
            or parsed_ip.is_link_local
            or parsed_ip.is_reserved
            or parsed_ip.is_multicast
        ):
            raise RuntimeError("Webhook target IP is not allowed.")

    def send_user_registered_webhook(
        self,
        *,
        user_id: object,
        username: object,
        email: object,
    ) -> None:
        if not settings.webhook.user_registered_url:
            raise RuntimeError("WEBHOOK__USER_REGISTERED_URL is not configured.")
        self._validate_url(settings.webhook.user_registered_url)
        policy = get_event_retry_policy("webhook.user_registered", provider_name="webhook")

        headers = {"Content-Type": "application/json"}
        if settings.webhook.auth_header_name and settings.webhook.auth_header_value:
            headers[settings.webhook.auth_header_name] = settings.webhook.auth_header_value

        payload = json.dumps(
            {
                "event": "user.registered",
                "user_id": user_id,
                "username": username,
                "email": email,
            }
        ).encode("utf-8")
        req = request.Request(
            settings.webhook.user_registered_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        retry_call(
            lambda: request.urlopen(req, timeout=settings.webhook.timeout_seconds),
            is_retryable=lambda exc: is_retryable_http_error(exc, policy=policy),
            policy=policy,
        ).close()

        logger.info(
            "sent user registered webhook",
            extra={
                "event_type": "webhook",
                "task_name": "webhook.user_registered",
                "user_id": user_id,
                "username": username,
                "email": email,
            },
        )

    def send_worker_failure_alert(
        self,
        *,
        task_name: object,
        task_id: object,
        error_message: object,
    ) -> None:
        raise RuntimeError("Generic webhook provider does not support worker failure alerts.")


class SlackWebhookProvider:
    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        allowed_hosts = settings.webhook.allowed_hosts or ["hooks.slack.com"]

        if settings.webhook.require_https and parsed.scheme != "https":
            raise RuntimeError("Slack webhook URL must use https.")
        if not hostname or hostname not in allowed_hosts:
            raise RuntimeError("Slack webhook target host is not allowed.")

    def _resolve_webhook_url(self, event_name: str) -> str:
        return settings.webhook.slack_route_urls.get(
            event_name,
            settings.webhook.slack_webhook_url or "",
        )

    def _build_payload(
        self,
        *,
        event_name: str,
        user_id: object,
        username: object,
        email: object,
        task_name: object | None = None,
        task_id: object | None = None,
        error_message: object | None = None,
    ) -> dict[str, object]:
        formatter = SLACK_FORMATTERS.get(event_name)
        if formatter is None:
            return {"text": f"Unhandled Slack event {event_name}"}
        if event_name == "worker_failure":
            payload = formatter(
                task_name=task_name,
                task_id=task_id,
                error_message=error_message,
            )
        else:
            payload = formatter(user_id=user_id, username=username, email=email)
        if settings.webhook.slack_channel:
            payload["channel"] = settings.webhook.slack_channel
        if settings.webhook.slack_username:
            payload["username"] = settings.webhook.slack_username
        if settings.webhook.slack_icon_emoji:
            payload["icon_emoji"] = settings.webhook.slack_icon_emoji
        return payload

    def send_user_registered_webhook(
        self,
        *,
        user_id: object,
        username: object,
        email: object,
    ) -> None:
        webhook_url = self._resolve_webhook_url("user_registered")
        if not webhook_url:
            raise RuntimeError("WEBHOOK__SLACK_WEBHOOK_URL is not configured.")
        self._validate_url(webhook_url)
        policy = get_event_retry_policy("webhook.user_registered", provider_name="webhook")

        payload = self._build_payload(
            event_name="user_registered",
            user_id=user_id,
            username=username,
            email=email,
        )

        req = request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        retry_call(
            lambda: request.urlopen(req, timeout=settings.webhook.timeout_seconds),
            is_retryable=lambda exc: is_retryable_http_error(exc, policy=policy),
            policy=policy,
        ).close()

        logger.info(
            "sent user registered webhook",
            extra={
                "event_type": "webhook",
                "provider": "slack",
                "task_name": "webhook.user_registered",
                "user_id": user_id,
                "username": username,
                "email": email,
            },
        )

    def send_worker_failure_alert(
        self,
        *,
        task_name: object,
        task_id: object,
        error_message: object,
    ) -> None:
        webhook_url = self._resolve_webhook_url("worker_failure")
        if not webhook_url:
            raise RuntimeError("WEBHOOK__SLACK_WEBHOOK_URL is not configured.")
        self._validate_url(webhook_url)
        policy = get_event_retry_policy(
            "webhook.worker_failure_alert",
            provider_name="webhook",
        )

        payload = self._build_payload(
            event_name="worker_failure",
            user_id="n/a",
            username="n/a",
            email="n/a",
            task_name=task_name,
            task_id=task_id,
            error_message=error_message,
        )
        req = request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        retry_call(
            lambda: request.urlopen(req, timeout=settings.webhook.timeout_seconds),
            is_retryable=lambda exc: is_retryable_http_error(exc, policy=policy),
            policy=policy,
        ).close()

        logger.info(
            "sent worker failure alert webhook",
            extra={
                "event_type": "webhook",
                "provider": "slack",
                "task_name": "webhook.worker_failure_alert",
                "failed_task_name": task_name,
                "failed_task_id": task_id,
            },
        )


def get_webhook_provider() -> WebhookProvider:
    if not settings.webhook.enabled or settings.webhook.dry_run:
        return ConsoleWebhookProvider()

    if settings.webhook.provider == "slack":
        return SlackWebhookProvider()
    return HTTPWebhookProvider()
