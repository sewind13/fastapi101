import json

from pydantic import BaseModel, Field, field_validator


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


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./database.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800


class OpsSettings(BaseModel):
    enabled: bool = True
