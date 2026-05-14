import json

from pydantic import BaseModel, Field, field_validator


class EmailSettings(BaseModel):
    enabled: bool = False
    dry_run: bool = True
    provider: str = "smtp"
    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    use_tls: bool = True
    from_email: str = "no-reply@example.com"
    sendgrid_api_key: str | None = None
    sendgrid_api_base_url: str = "https://api.sendgrid.com/v3/mail/send"
    sendgrid_timeout_seconds: float = 10.0
    sendgrid_categories: list[str] = Field(default_factory=list)
    sendgrid_custom_args: dict[str, str] = Field(default_factory=dict)
    sendgrid_welcome_template_id: str | None = None
    sendgrid_password_reset_template_id: str | None = None
    sendgrid_verification_template_id: str | None = None
    ses_region: str | None = None
    ses_configuration_set: str | None = None
    ses_profile_name: str | None = None
    ses_access_key_id: str | None = None
    ses_secret_access_key: str | None = None
    ses_session_token: str | None = None
    ses_welcome_template_name: str | None = None
    ses_password_reset_template_name: str | None = None
    ses_verification_template_name: str | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"smtp", "sendgrid", "ses"}:
            raise ValueError("EMAIL__PROVIDER must be 'smtp', 'sendgrid', or 'ses'.")
        return normalized

    @field_validator("sendgrid_categories", mode="before")
    @classmethod
    def parse_sendgrid_categories(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("sendgrid_custom_args", mode="before")
    @classmethod
    def parse_sendgrid_custom_args(cls, value: str | dict[str, str] | None) -> dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return {}
            return json.loads(value)
        return value


class WebhookSettings(BaseModel):
    enabled: bool = False
    dry_run: bool = True
    provider: str = "generic"
    user_registered_url: str | None = None
    timeout_seconds: float = 5.0
    auth_header_name: str | None = None
    auth_header_value: str | None = None
    slack_webhook_url: str | None = None
    slack_channel: str | None = None
    slack_username: str | None = None
    slack_icon_emoji: str | None = None
    slack_route_urls: dict[str, str] = Field(default_factory=dict)
    allowed_hosts: list[str] = Field(default_factory=list)
    allow_private_targets: bool = False
    require_https: bool = True

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"generic", "slack"}:
            raise ValueError("WEBHOOK__PROVIDER must be 'generic' or 'slack'.")
        return normalized

    @field_validator("slack_route_urls", mode="before")
    @classmethod
    def parse_slack_route_urls(cls, value: str | dict[str, str] | None) -> dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return {}
            return json.loads(value)
        return value

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return [item.strip().lower() for item in value if item.strip()]
