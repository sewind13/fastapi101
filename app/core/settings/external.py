import json

from pydantic import BaseModel, Field, field_validator


class ExternalSettings(BaseModel):
    timeout_seconds: float = 10.0
    max_attempts: int = 3
    backoff_seconds: float = 0.5
    max_backoff_seconds: float = 5.0
    retry_on_statuses: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    @field_validator("retry_on_statuses", mode="before")
    @classmethod
    def parse_retry_on_statuses(cls, value: str | list[int] | None) -> list[int]:
        if value is None:
            return [429, 500, 502, 503, 504]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return [429, 500, 502, 503, 504]
            if value.startswith("["):
                return json.loads(value)
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value


class ProviderRetryPolicy(BaseModel):
    timeout_seconds: float = 10.0
    max_attempts: int = 3
    backoff_seconds: float = 0.5
    max_backoff_seconds: float = 5.0
    retry_on_statuses: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    @field_validator("retry_on_statuses", mode="before")
    @classmethod
    def parse_retry_on_statuses(cls, value: str | list[int] | None) -> list[int]:
        return ExternalSettings.parse_retry_on_statuses(value)


class ExternalPoliciesSettings(BaseModel):
    smtp: ProviderRetryPolicy = Field(default_factory=ProviderRetryPolicy)
    sendgrid: ProviderRetryPolicy = Field(default_factory=ProviderRetryPolicy)
    ses: ProviderRetryPolicy = Field(default_factory=ProviderRetryPolicy)
    webhook: ProviderRetryPolicy = Field(default_factory=ProviderRetryPolicy)


class ExternalEventPoliciesSettings(BaseModel):
    email_send_welcome: ProviderRetryPolicy | None = None
    email_send_password_reset: ProviderRetryPolicy | None = None
    email_send_verification: ProviderRetryPolicy | None = None
    webhook_user_registered: ProviderRetryPolicy | None = None
    webhook_worker_failure_alert: ProviderRetryPolicy | None = None
