import json
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-to-a-32-character-minimum-secret"
DEFAULT_ISSUER = "fastapi-template"
DEFAULT_AUDIENCE = "fastapi-template-users"


class AppSettings(BaseModel):
    name: str = "FastAPI Template"
    debug: bool = False
    env: str = "development"
    public_base_url: str = "http://localhost:8000"


class ExampleSettings(BaseModel):
    enable_items_module: bool = True


class APISettings(BaseModel):
    v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)
    public_registration_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []

            if value.startswith("["):
                return json.loads(value)

            return [origin.strip() for origin in value.split(",") if origin.strip()]

        return value


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


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./database.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800


class LoggingSettings(BaseModel):
    level: str = "INFO"
    audit_level: str = "INFO"
    schema_version: str = "1.0"
    access_log_sample_rate: float = 1.0
    access_log_skip_paths: list[str] = Field(default_factory=lambda: ["/health/live"])
    access_log_skip_prefixes: list[str] = Field(default_factory=list)
    trace_header_name: str = "traceparent"

    @field_validator("access_log_skip_paths", "access_log_skip_prefixes", mode="before")
    @classmethod
    def parse_skip_paths(cls, value: str | list[str] | None) -> list[str]:
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

    @field_validator("access_log_sample_rate")
    @classmethod
    def validate_sample_rate(cls, value: float) -> float:
        return min(max(value, 0.0), 1.0)


class TelemetrySettings(BaseModel):
    enabled: bool = False
    service_name: str = "fastapi-template"
    service_version: str = "0.1.0"
    exporter_otlp_endpoint: str | None = None
    exporter_otlp_insecure: bool = True


class HealthSettings(BaseModel):
    timeout_seconds: float = 2.0
    enable_redis_check: bool = False
    redis_url: str | None = None
    enable_s3_check: bool = False
    s3_endpoint_url: str | None = None
    s3_bucket_name: str | None = None
    s3_region: str | None = None
    enable_queue_check: bool = False
    queue_url: str | None = None


class MetricsSettings(BaseModel):
    enabled: bool = True
    path: str = "/metrics"
    include_in_schema: bool = False
    auth_token: str | None = None


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


class CacheSettings(BaseModel):
    enabled: bool = False
    backend: str = "memory"
    redis_url: str | None = None
    key_prefix: str = "cache"
    default_ttl_seconds: int = 60
    items_list_ttl_seconds: int = 30

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("CACHE__BACKEND must be either 'memory' or 'redis'.")
        return normalized


class OpsSettings(BaseModel):
    enabled: bool = True


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


class WorkerSettings(BaseModel):
    enabled: bool = False
    broker_url: str | None = None
    queue_name: str = "app.default"
    retry_queue_name: str = "app.default.retry"
    dead_letter_queue_name: str = "app.default.dlq"
    prefetch_count: int = 10
    max_retries: int = 3
    retry_delay_ms: int = 30000
    max_retry_delay_ms: int = 300000
    requeue_on_failure: bool = False
    idempotency_enabled: bool = True
    idempotency_backend: str = "memory"
    idempotency_redis_url: str | None = None
    idempotency_key_prefix: str = "worker_idempotency"
    idempotency_ttl_seconds: int = 86400

    @field_validator("idempotency_backend")
    @classmethod
    def validate_idempotency_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError(
                "WORKER__IDEMPOTENCY_BACKEND must be either 'memory' or 'redis'."
            )
        return normalized


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    examples: ExampleSettings = Field(default_factory=ExampleSettings)
    api: APISettings = Field(default_factory=APISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    auth_rate_limit: AuthRateLimitSettings = Field(default_factory=AuthRateLimitSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    health: HealthSettings = Field(default_factory=HealthSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    external: ExternalSettings = Field(default_factory=ExternalSettings)
    external_policies: ExternalPoliciesSettings = Field(default_factory=ExternalPoliciesSettings)
    external_event_policies: ExternalEventPoliciesSettings = Field(
        default_factory=ExternalEventPoliciesSettings
    )
    cache: CacheSettings = Field(default_factory=CacheSettings)
    ops: OpsSettings = Field(default_factory=OpsSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    webhook: WebhookSettings = Field(default_factory=WebhookSettings)
    worker: WorkerSettings = Field(default_factory=WorkerSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    @model_validator(mode="before")
    @classmethod
    def support_legacy_flat_env(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        data = dict(data)

        def promote(section_name: str, mapping: dict[str, str]) -> None:
            section = dict(data.get(section_name) or {})
            for legacy_key, nested_key in mapping.items():
                if legacy_key in data and nested_key not in section:
                    section[nested_key] = data[legacy_key]
            if section:
                data[section_name] = section

        promote(
            "app",
            {
                "APP_NAME": "name",
                "DEBUG": "debug",
                "PUBLIC_BASE_URL": "public_base_url",
            },
        )
        promote(
            "examples",
            {
                "ENABLE_ITEMS_MODULE": "enable_items_module",
            },
        )
        promote(
            "api",
            {
                "API_V1_STR": "v1_prefix",
                "CORS_ORIGINS": "cors_origins",
                "PUBLIC_REGISTRATION_ENABLED": "public_registration_enabled",
            },
        )
        promote(
            "security",
            {
                "SECRET_KEY": "secret_key",
                "ALGORITHM": "algorithm",
                "JWT_ISSUER": "issuer",
                "JWT_AUDIENCE": "audience",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "access_token_expire_minutes",
                "REFRESH_TOKEN_EXPIRE_MINUTES": "refresh_token_expire_minutes",
                "PASSWORD_MIN_LENGTH": "password_min_length",
                "PASSWORD_REQUIRE_UPPERCASE": "password_require_uppercase",
                "PASSWORD_REQUIRE_LOWERCASE": "password_require_lowercase",
                "PASSWORD_REQUIRE_DIGIT": "password_require_digit",
                "PASSWORD_REQUIRE_SPECIAL": "password_require_special",
                "PASSWORD_FORBID_USERNAME": "password_forbid_username",
                "PASSWORD_FORBID_EMAIL_LOCALPART": "password_forbid_email_localpart",
                "EMAIL_VERIFICATION_ENABLED": "email_verification_enabled",
                "EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES": (
                    "email_verification_token_expire_minutes"
                ),
                "REQUIRE_VERIFIED_EMAIL_FOR_LOGIN": "require_verified_email_for_login",
            },
        )
        promote(
            "auth_rate_limit",
            {
                "AUTH_RATE_LIMIT_ENABLED": "enabled",
                "AUTH_RATE_LIMIT_BACKEND": "backend",
                "AUTH_RATE_LIMIT_REDIS_URL": "redis_url",
                "AUTH_RATE_LIMIT_KEY_PREFIX": "key_prefix",
                "AUTH_RATE_LIMIT_TRUST_PROXY_HEADERS": "trust_proxy_headers",
                "AUTH_RATE_LIMIT_TRUSTED_PROXY_CIDRS": "trusted_proxy_cidrs",
                "AUTH_ACCOUNT_LOCKOUT_ENABLED": "account_lockout_enabled",
                "AUTH_ACCOUNT_LOCKOUT_MAX_ATTEMPTS": "account_lockout_max_attempts",
                "AUTH_ACCOUNT_LOCKOUT_SECONDS": "account_lockout_seconds",
                "AUTH_LOGIN_MAX_ATTEMPTS": "login_max_attempts",
                "AUTH_LOGIN_WINDOW_SECONDS": "login_window_seconds",
                "AUTH_TOKEN_MAX_ATTEMPTS": "token_max_attempts",
                "AUTH_TOKEN_WINDOW_SECONDS": "token_window_seconds",
            },
        )
        promote(
            "database",
            {
                "DATABASE_URL": "url",
                "DATABASE_ECHO": "echo",
            },
        )
        promote(
            "logging",
            {
                "LOG_LEVEL": "level",
                "AUDIT_LOG_LEVEL": "audit_level",
                "LOG_SCHEMA_VERSION": "schema_version",
                "ACCESS_LOG_SAMPLE_RATE": "access_log_sample_rate",
                "ACCESS_LOG_SKIP_PATHS": "access_log_skip_paths",
                "ACCESS_LOG_SKIP_PREFIXES": "access_log_skip_prefixes",
                "TRACE_HEADER_NAME": "trace_header_name",
            },
        )
        promote(
            "telemetry",
            {
                "OTEL_ENABLED": "enabled",
                "OTEL_SERVICE_NAME": "service_name",
                "OTEL_SERVICE_VERSION": "service_version",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "exporter_otlp_endpoint",
                "OTEL_EXPORTER_OTLP_INSECURE": "exporter_otlp_insecure",
            },
        )
        promote(
            "health",
            {
                "HEALTH_TIMEOUT_SECONDS": "timeout_seconds",
                "ENABLE_REDIS_CHECK": "enable_redis_check",
                "REDIS_URL": "redis_url",
                "ENABLE_S3_CHECK": "enable_s3_check",
                "S3_ENDPOINT_URL": "s3_endpoint_url",
                "S3_BUCKET_NAME": "s3_bucket_name",
                "S3_REGION": "s3_region",
                "ENABLE_QUEUE_CHECK": "enable_queue_check",
                "QUEUE_URL": "queue_url",
            },
        )
        promote(
            "metrics",
            {
                "METRICS_ENABLED": "enabled",
                "METRICS_PATH": "path",
                "METRICS_INCLUDE_IN_SCHEMA": "include_in_schema",
            },
        )
        promote(
            "external",
            {
                "EXTERNAL_TIMEOUT_SECONDS": "timeout_seconds",
                "EXTERNAL_MAX_ATTEMPTS": "max_attempts",
                "EXTERNAL_BACKOFF_SECONDS": "backoff_seconds",
                "EXTERNAL_MAX_BACKOFF_SECONDS": "max_backoff_seconds",
                "EXTERNAL_RETRY_ON_STATUSES": "retry_on_statuses",
            },
        )
        promote(
            "external_policies",
            {
                "SMTP_TIMEOUT_SECONDS": "smtp.timeout_seconds",
                "SMTP_MAX_ATTEMPTS": "smtp.max_attempts",
                "SMTP_BACKOFF_SECONDS": "smtp.backoff_seconds",
                "SMTP_MAX_BACKOFF_SECONDS": "smtp.max_backoff_seconds",
                "SMTP_RETRY_ON_STATUSES": "smtp.retry_on_statuses",
                "SENDGRID_TIMEOUT_SECONDS": "sendgrid.timeout_seconds",
                "SENDGRID_MAX_ATTEMPTS": "sendgrid.max_attempts",
                "SENDGRID_BACKOFF_SECONDS": "sendgrid.backoff_seconds",
                "SENDGRID_MAX_BACKOFF_SECONDS": "sendgrid.max_backoff_seconds",
                "SENDGRID_RETRY_ON_STATUSES": "sendgrid.retry_on_statuses",
                "SES_TIMEOUT_SECONDS": "ses.timeout_seconds",
                "SES_MAX_ATTEMPTS": "ses.max_attempts",
                "SES_BACKOFF_SECONDS": "ses.backoff_seconds",
                "SES_MAX_BACKOFF_SECONDS": "ses.max_backoff_seconds",
                "SES_RETRY_ON_STATUSES": "ses.retry_on_statuses",
                "WEBHOOK_TIMEOUT_SECONDS_POLICY": "webhook.timeout_seconds",
                "WEBHOOK_MAX_ATTEMPTS": "webhook.max_attempts",
                "WEBHOOK_BACKOFF_SECONDS": "webhook.backoff_seconds",
                "WEBHOOK_MAX_BACKOFF_SECONDS": "webhook.max_backoff_seconds",
                "WEBHOOK_RETRY_ON_STATUSES": "webhook.retry_on_statuses",
            },
        )
        promote(
            "cache",
            {
                "CACHE_ENABLED": "enabled",
                "CACHE_BACKEND": "backend",
                "CACHE_REDIS_URL": "redis_url",
                "CACHE_KEY_PREFIX": "key_prefix",
                "CACHE_DEFAULT_TTL_SECONDS": "default_ttl_seconds",
                "CACHE_ITEMS_LIST_TTL_SECONDS": "items_list_ttl_seconds",
            },
        )
        promote(
            "ops",
            {
                "OPS_ENABLED": "enabled",
            },
        )
        promote(
            "email",
            {
                "EMAIL_ENABLED": "enabled",
                "EMAIL_DRY_RUN": "dry_run",
                "EMAIL_PROVIDER": "provider",
                "EMAIL_HOST": "host",
                "EMAIL_PORT": "port",
                "EMAIL_USERNAME": "username",
                "EMAIL_PASSWORD": "password",
                "EMAIL_USE_TLS": "use_tls",
                "EMAIL_FROM_EMAIL": "from_email",
                "EMAIL_SENDGRID_API_KEY": "sendgrid_api_key",
                "EMAIL_SENDGRID_API_BASE_URL": "sendgrid_api_base_url",
                "EMAIL_SENDGRID_TIMEOUT_SECONDS": "sendgrid_timeout_seconds",
                "EMAIL_SENDGRID_CATEGORIES": "sendgrid_categories",
                "EMAIL_SENDGRID_CUSTOM_ARGS": "sendgrid_custom_args",
                "EMAIL_SENDGRID_WELCOME_TEMPLATE_ID": "sendgrid_welcome_template_id",
                "EMAIL_SENDGRID_PASSWORD_RESET_TEMPLATE_ID": "sendgrid_password_reset_template_id",
                "EMAIL_SENDGRID_VERIFICATION_TEMPLATE_ID": "sendgrid_verification_template_id",
                "EMAIL_SES_REGION": "ses_region",
                "EMAIL_SES_CONFIGURATION_SET": "ses_configuration_set",
                "EMAIL_SES_PROFILE_NAME": "ses_profile_name",
                "EMAIL_SES_ACCESS_KEY_ID": "ses_access_key_id",
                "EMAIL_SES_SECRET_ACCESS_KEY": "ses_secret_access_key",
                "EMAIL_SES_SESSION_TOKEN": "ses_session_token",
                "EMAIL_SES_WELCOME_TEMPLATE_NAME": "ses_welcome_template_name",
                "EMAIL_SES_PASSWORD_RESET_TEMPLATE_NAME": "ses_password_reset_template_name",
                "EMAIL_SES_VERIFICATION_TEMPLATE_NAME": "ses_verification_template_name",
            },
        )
        promote(
            "webhook",
            {
                "WEBHOOK_ENABLED": "enabled",
                "WEBHOOK_DRY_RUN": "dry_run",
                "WEBHOOK_PROVIDER": "provider",
                "WEBHOOK_USER_REGISTERED_URL": "user_registered_url",
                "WEBHOOK_TIMEOUT_SECONDS": "timeout_seconds",
                "WEBHOOK_AUTH_HEADER_NAME": "auth_header_name",
                "WEBHOOK_AUTH_HEADER_VALUE": "auth_header_value",
                "WEBHOOK_SLACK_WEBHOOK_URL": "slack_webhook_url",
                "WEBHOOK_SLACK_CHANNEL": "slack_channel",
                "WEBHOOK_SLACK_USERNAME": "slack_username",
                "WEBHOOK_SLACK_ICON_EMOJI": "slack_icon_emoji",
                "WEBHOOK_SLACK_ROUTE_URLS": "slack_route_urls",
                "WEBHOOK_ALLOWED_HOSTS": "allowed_hosts",
                "WEBHOOK_ALLOW_PRIVATE_TARGETS": "allow_private_targets",
                "WEBHOOK_REQUIRE_HTTPS": "require_https",
            },
        )
        promote(
            "worker",
            {
                "WORKER_ENABLED": "enabled",
                "WORKER_BROKER_URL": "broker_url",
                "WORKER_QUEUE_NAME": "queue_name",
                "WORKER_RETRY_QUEUE_NAME": "retry_queue_name",
                "WORKER_DEAD_LETTER_QUEUE_NAME": "dead_letter_queue_name",
                "WORKER_PREFETCH_COUNT": "prefetch_count",
                "WORKER_MAX_RETRIES": "max_retries",
                "WORKER_RETRY_DELAY_MS": "retry_delay_ms",
                "WORKER_MAX_RETRY_DELAY_MS": "max_retry_delay_ms",
                "WORKER_REQUEUE_ON_FAILURE": "requeue_on_failure",
                "WORKER_IDEMPOTENCY_ENABLED": "idempotency_enabled",
                "WORKER_IDEMPOTENCY_BACKEND": "idempotency_backend",
                "WORKER_IDEMPOTENCY_REDIS_URL": "idempotency_redis_url",
                "WORKER_IDEMPOTENCY_KEY_PREFIX": "idempotency_key_prefix",
                "WORKER_IDEMPOTENCY_TTL_SECONDS": "idempotency_ttl_seconds",
            },
        )

        return data

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app.env.lower() != "production":
            return self

        errors: list[str] = []

        if self.app.debug:
            errors.append("APP__DEBUG must be false in production.")

        if self.security.secret_key == DEFAULT_SECRET_KEY or len(self.security.secret_key) < 32:
            errors.append(
                "SECURITY__SECRET_KEY must be replaced with a strong secret "
                "that is at least 32 characters long."
            )

        if self.security.issuer == DEFAULT_ISSUER:
            errors.append("SECURITY__ISSUER must be set to a production-specific value.")

        if self.security.audience == DEFAULT_AUDIENCE:
            errors.append("SECURITY__AUDIENCE must be set to a production-specific value.")

        if self.security.email_verification_enabled and not self.app.public_base_url:
            errors.append(
                "APP__PUBLIC_BASE_URL must be configured when "
                "SECURITY__EMAIL_VERIFICATION_ENABLED=true."
            )

        if self.database.url.startswith("sqlite"):
            errors.append(
                "DATABASE__URL must point to a production database and "
                "cannot use SQLite."
            )

        if not self.api.cors_origins:
            errors.append("API__CORS_ORIGINS must be explicitly configured in production.")

        if self.auth_rate_limit.enabled:
            if self.auth_rate_limit.backend != "redis":
                errors.append(
                    "AUTH_RATE_LIMIT__BACKEND must be 'redis' in production "
                    "to support multi-instance deployments."
                )
            if not self.auth_rate_limit.redis_url:
                errors.append(
                    "AUTH_RATE_LIMIT__REDIS_URL must be configured when "
                    "production rate limiting is enabled."
                )

        if self.cache.enabled and self.cache.backend == "redis" and not self.cache.redis_url:
            errors.append(
                "CACHE__REDIS_URL must be configured when CACHE__ENABLED=true "
                "and CACHE__BACKEND='redis'."
            )

        if self.metrics.enabled and not self.metrics.auth_token:
            errors.append(
                "METRICS__AUTH_TOKEN must be configured when METRICS__ENABLED=true "
                "in production."
            )

        if self.webhook.enabled and not self.webhook.dry_run:
            if self.webhook.provider == "generic" and not self.webhook.allowed_hosts:
                errors.append(
                    "WEBHOOK__ALLOWED_HOSTS must be configured when WEBHOOK__ENABLED=true, "
                    "WEBHOOK__DRY_RUN=false, and WEBHOOK__PROVIDER='generic' in production."
                )

        if self.api.public_registration_enabled and self.ops.enabled:
            errors.append(
                "API__PUBLIC_REGISTRATION_ENABLED should be false in production when "
                "operations endpoints are enabled."
            )

        if self.worker.enabled and not self.worker.broker_url:
            errors.append("WORKER__BROKER_URL must be configured when WORKER__ENABLED=true.")

        if (
            self.worker.enabled
            and self.worker.idempotency_enabled
            and self.worker.idempotency_backend == "redis"
            and not self.worker.idempotency_redis_url
        ):
            errors.append(
                "WORKER__IDEMPOTENCY_REDIS_URL must be configured when "
                "WORKER__IDEMPOTENCY_ENABLED=true and WORKER__IDEMPOTENCY_BACKEND='redis'."
            )

        if errors:
            raise ValueError(" ".join(errors))

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
