from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.settings.base import (
    APISettings,
    AppSettings,
    DatabaseSettings,
    ExampleSettings,
    OpsSettings,
)
from app.core.settings.compat import promote_legacy_flat_env
from app.core.settings.delivery import EmailSettings, WebhookSettings
from app.core.settings.external import (
    ExternalEventPoliciesSettings,
    ExternalPoliciesSettings,
    ExternalSettings,
)
from app.core.settings.observability import (
    CacheSettings,
    HealthSettings,
    LoggingSettings,
    MetricsSettings,
    TelemetrySettings,
)
from app.core.settings.security import AuthRateLimitSettings, SecuritySettings
from app.core.settings.validation import validate_production_settings
from app.core.settings.worker import WorkerSettings


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
        return promote_legacy_flat_env(data)

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        return validate_production_settings(self)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
