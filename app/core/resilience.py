from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from urllib.error import HTTPError, URLError

from app.core.config import settings


@dataclass(frozen=True)
class RetryPolicy:
    timeout_seconds: float
    max_attempts: int
    backoff_seconds: float
    max_backoff_seconds: float
    retry_on_statuses: tuple[int, ...]


def get_retry_policy(name: str) -> RetryPolicy:
    policies = settings.external_policies
    selected = getattr(policies, name, None)
    if selected is not None:
        return RetryPolicy(
            timeout_seconds=selected.timeout_seconds,
            max_attempts=selected.max_attempts,
            backoff_seconds=selected.backoff_seconds,
            max_backoff_seconds=selected.max_backoff_seconds,
            retry_on_statuses=tuple(selected.retry_on_statuses),
        )
    return RetryPolicy(
        timeout_seconds=settings.external.timeout_seconds,
        max_attempts=settings.external.max_attempts,
        backoff_seconds=settings.external.backoff_seconds,
        max_backoff_seconds=settings.external.max_backoff_seconds,
        retry_on_statuses=tuple(settings.external.retry_on_statuses),
    )


EVENT_POLICY_MAP = {
    "email.send_welcome": "email_send_welcome",
    "email.send_password_reset": "email_send_password_reset",
    "email.send_verification": "email_send_verification",
    "webhook.user_registered": "webhook_user_registered",
    "webhook.worker_failure_alert": "webhook_worker_failure_alert",
}


def get_event_retry_policy(event_name: str, *, provider_name: str) -> RetryPolicy:
    selected_name = EVENT_POLICY_MAP.get(event_name)
    if selected_name:
        selected = getattr(settings.external_event_policies, selected_name, None)
        if selected is not None:
            return RetryPolicy(
                timeout_seconds=selected.timeout_seconds,
                max_attempts=selected.max_attempts,
                backoff_seconds=selected.backoff_seconds,
                max_backoff_seconds=selected.max_backoff_seconds,
                retry_on_statuses=tuple(selected.retry_on_statuses),
            )
    return get_retry_policy(provider_name)


def _sleep_for_attempt(attempt: int, *, policy: RetryPolicy) -> None:
    delay = min(
        policy.backoff_seconds * (2 ** max(attempt - 1, 0)),
        policy.max_backoff_seconds,
    )
    sleep(delay)


def is_retryable_http_error(exc: Exception, *, policy: RetryPolicy) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code in policy.retry_on_statuses
    if isinstance(exc, URLError | TimeoutError):
        return True
    return False


def retry_call[T](
    func: Callable[[], T],
    *,
    is_retryable: Callable[[Exception], bool],
    policy: RetryPolicy,
) -> T:
    attempts = max(policy.max_attempts, 1)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt >= attempts or not is_retryable(exc):
                raise
            _sleep_for_attempt(attempt, policy=policy)

    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_call exhausted without returning or raising.")
