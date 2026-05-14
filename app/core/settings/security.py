import json

from pydantic import BaseModel, Field, field_validator

from app.core.settings.constants import DEFAULT_AUDIENCE, DEFAULT_ISSUER, DEFAULT_SECRET_KEY


class SecuritySettings(BaseModel):
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    issuer: str = DEFAULT_ISSUER
    audience: str = DEFAULT_AUDIENCE
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    password_min_length: int = 8
    password_require_uppercase: bool = False
    password_require_lowercase: bool = True
    password_require_digit: bool = False
    password_require_special: bool = False
    password_forbid_username: bool = True
    password_forbid_email_localpart: bool = True
    email_verification_enabled: bool = True
    email_verification_token_expire_minutes: int = 60 * 24
    require_verified_email_for_login: bool = False


class AuthRateLimitSettings(BaseModel):
    enabled: bool = True
    backend: str = "memory"
    redis_url: str | None = None
    key_prefix: str = "rate_limit"
    trust_proxy_headers: bool = False
    trusted_proxy_cidrs: list[str] = Field(default_factory=list)
    account_lockout_enabled: bool = True
    account_lockout_max_attempts: int = 5
    account_lockout_seconds: int = 900
    login_max_attempts: int = 5
    login_window_seconds: int = 300
    token_max_attempts: int = 20
    token_window_seconds: int = 60

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("AUTH_RATE_LIMIT__BACKEND must be either 'memory' or 'redis'.")
        return normalized

    @field_validator("trusted_proxy_cidrs", mode="before")
    @classmethod
    def parse_trusted_proxy_cidrs(cls, value: str | list[str] | None) -> list[str]:
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
