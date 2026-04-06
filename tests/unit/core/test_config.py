import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(**overrides) -> Settings:
    base = {
        "app": {
            "name": "FastAPI Template",
            "debug": False,
            "env": "development",
        },
        "api": {
            "v1_prefix": "/api/v1",
            "cors_origins": [],
            "public_registration_enabled": False,
        },
        "security": {
            "secret_key": "x" * 32,
            "algorithm": "HS256",
            "issuer": "template-prod",
            "audience": "template-users",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_minutes": 10080,
        },
        "auth_rate_limit": {
            "enabled": True,
            "backend": "redis",
            "redis_url": "redis://redis:6379/0",
            "key_prefix": "rate_limit",
            "login_max_attempts": 5,
            "login_window_seconds": 300,
            "token_max_attempts": 20,
            "token_window_seconds": 60,
        },
        "database": {
            "url": "postgresql+psycopg://app:app@db:5432/app",
            "echo": False,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        },
        "worker": {
            "enabled": False,
            "broker_url": None,
            "queue_name": "app.default",
            "retry_queue_name": "app.default.retry",
            "dead_letter_queue_name": "app.default.dlq",
            "prefetch_count": 10,
            "max_retries": 3,
            "retry_delay_ms": 30000,
            "max_retry_delay_ms": 300000,
            "requeue_on_failure": False,
            "idempotency_enabled": True,
            "idempotency_backend": "memory",
            "idempotency_redis_url": None,
            "idempotency_key_prefix": "worker_idempotency",
            "idempotency_ttl_seconds": 86400,
        },
        "external": {
            "timeout_seconds": 10.0,
            "max_attempts": 3,
            "backoff_seconds": 0.5,
            "max_backoff_seconds": 5.0,
            "retry_on_statuses": [429, 500, 502, 503, 504],
        },
        "external_policies": {
            "smtp": {
                "timeout_seconds": 10.0,
                "max_attempts": 3,
                "backoff_seconds": 0.5,
                "max_backoff_seconds": 5.0,
                "retry_on_statuses": [429, 500, 502, 503, 504],
            },
            "sendgrid": {
                "timeout_seconds": 10.0,
                "max_attempts": 3,
                "backoff_seconds": 0.5,
                "max_backoff_seconds": 5.0,
                "retry_on_statuses": [429, 500, 502, 503, 504],
            },
            "ses": {
                "timeout_seconds": 10.0,
                "max_attempts": 3,
                "backoff_seconds": 0.5,
                "max_backoff_seconds": 5.0,
                "retry_on_statuses": [429, 500, 502, 503, 504],
            },
            "webhook": {
                "timeout_seconds": 10.0,
                "max_attempts": 3,
                "backoff_seconds": 0.5,
                "max_backoff_seconds": 5.0,
                "retry_on_statuses": [429, 500, 502, 503, 504],
            },
        },
        "external_event_policies": {},
        "metrics": {
            "enabled": True,
            "path": "/metrics",
            "include_in_schema": False,
            "auth_token": "metrics-secret",
        },
        "webhook": {
            "enabled": False,
            "dry_run": True,
            "provider": "generic",
            "user_registered_url": None,
            "timeout_seconds": 5.0,
            "auth_header_name": None,
            "auth_header_value": None,
            "slack_webhook_url": None,
            "slack_channel": None,
            "slack_username": None,
            "slack_icon_emoji": None,
            "slack_route_urls": {},
            "allowed_hosts": [],
            "allow_private_targets": False,
            "require_https": True,
        },
        "cache": {
            "enabled": True,
            "backend": "redis",
            "redis_url": "redis://redis:6379/2",
            "key_prefix": "cache",
            "default_ttl_seconds": 60,
            "items_list_ttl_seconds": 30,
        },
    }
    for key, value in overrides.items():
        base[key] = value
    return Settings.model_validate(base)


def test_production_settings_require_safe_values():
    with pytest.raises(ValidationError) as exc_info:
        build_settings(
            app={"name": "FastAPI Template", "debug": True, "env": "production"},
            api={
                "v1_prefix": "/api/v1",
                "cors_origins": [],
                "public_registration_enabled": True,
            },
            security={
                "secret_key": "change-me-to-a-32-character-minimum-secret",
                "algorithm": "HS256",
                "issuer": "fastapi-template",
                "audience": "fastapi-template-users",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_minutes": 10080,
            },
            auth_rate_limit={
                "enabled": True,
                "backend": "memory",
                "redis_url": None,
                "key_prefix": "rate_limit",
                "login_max_attempts": 5,
                "login_window_seconds": 300,
                "token_max_attempts": 20,
                "token_window_seconds": 60,
            },
            database={
                "url": "sqlite:///./database.db",
                "echo": False,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 1800,
            },
            cache={
                "enabled": True,
                "backend": "redis",
                "redis_url": None,
                "key_prefix": "cache",
                "default_ttl_seconds": 60,
                "items_list_ttl_seconds": 30,
            },
            metrics={
                "enabled": True,
                "path": "/metrics",
                "include_in_schema": False,
                "auth_token": None,
            },
            webhook={
                "enabled": True,
                "dry_run": False,
                "provider": "generic",
                "user_registered_url": "https://hooks.example.com/user-registered",
                "timeout_seconds": 5.0,
                "auth_header_name": None,
                "auth_header_value": None,
                "slack_webhook_url": None,
                "slack_channel": None,
                "slack_username": None,
                "slack_icon_emoji": None,
                "slack_route_urls": {},
                "allowed_hosts": [],
                "allow_private_targets": False,
                "require_https": True,
            },
        )

    message = str(exc_info.value)
    assert "APP__DEBUG must be false in production." in message
    assert "SECURITY__SECRET_KEY must be replaced" in message
    assert "SECURITY__ISSUER must be set" in message
    assert "SECURITY__AUDIENCE must be set" in message
    assert "AUTH_RATE_LIMIT__BACKEND must be 'redis' in production" in message
    assert "AUTH_RATE_LIMIT__REDIS_URL must be configured" in message
    assert "DATABASE__URL must point to a production database" in message
    assert "API__CORS_ORIGINS must be explicitly configured in production." in message
    assert "CACHE__REDIS_URL must be configured" in message
    assert "METRICS__AUTH_TOKEN must be configured" in message
    assert "WEBHOOK__ALLOWED_HOSTS must be configured" in message
    assert "API__PUBLIC_REGISTRATION_ENABLED should be false" in message


def test_non_local_environments_require_non_default_secret_key():
    with pytest.raises(ValidationError) as exc_info:
        build_settings(
            app={"name": "FastAPI Template", "debug": False, "env": "staging"},
            security={
                "secret_key": "change-me-to-a-32-character-minimum-secret",
                "algorithm": "HS256",
                "issuer": "template-staging",
                "audience": "template-users",
                "access_token_expire_minutes": 30,
                "refresh_token_expire_minutes": 10080,
            },
        )

    assert "SECURITY__SECRET_KEY must be replaced before deploying to non-local environments." in str(
        exc_info.value
    )


def test_local_like_environments_allow_default_secret_key_for_development():
    settings = build_settings(
        app={"name": "FastAPI Template", "debug": False, "env": "testing"},
        security={
            "secret_key": "change-me-to-a-32-character-minimum-secret",
            "algorithm": "HS256",
            "issuer": "template-testing",
            "audience": "template-users",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_minutes": 10080,
        },
    )

    assert settings.app.env == "testing"
    assert settings.security.secret_key == "change-me-to-a-32-character-minimum-secret"


def test_production_settings_accept_safe_values():
    settings = build_settings(
        app={"name": "FastAPI Template", "debug": False, "env": "production"},
        api={
            "v1_prefix": "/api/v1",
            "cors_origins": ["https://app.example.com"],
            "public_registration_enabled": False,
        },
        worker={
            "enabled": True,
            "broker_url": "amqp://guest:guest@queue:5672/",
            "queue_name": "app.default",
            "retry_queue_name": "app.default.retry",
            "dead_letter_queue_name": "app.default.dlq",
            "prefetch_count": 10,
            "max_retries": 3,
            "retry_delay_ms": 30000,
            "max_retry_delay_ms": 300000,
            "requeue_on_failure": False,
            "idempotency_enabled": True,
            "idempotency_backend": "redis",
            "idempotency_redis_url": "redis://redis:6379/1",
            "idempotency_key_prefix": "worker_idempotency",
            "idempotency_ttl_seconds": 86400,
        },
        webhook={
            "enabled": True,
            "dry_run": False,
            "provider": "generic",
            "user_registered_url": "https://hooks.example.com/user-registered",
            "timeout_seconds": 5.0,
            "auth_header_name": "X-Webhook-Token",
            "auth_header_value": "secret",
            "slack_webhook_url": None,
            "slack_channel": None,
            "slack_username": None,
            "slack_icon_emoji": None,
            "slack_route_urls": {},
            "allowed_hosts": ["hooks.example.com"],
            "allow_private_targets": False,
            "require_https": True,
        },
    )

    assert settings.app.env == "production"
    assert settings.api.cors_origins == ["https://app.example.com"]


def test_webhook_allowed_hosts_are_normalized():
    settings = build_settings(
        webhook={
            "enabled": False,
            "dry_run": True,
            "provider": "generic",
            "user_registered_url": None,
            "timeout_seconds": 5.0,
            "auth_header_name": None,
            "auth_header_value": None,
            "slack_webhook_url": None,
            "slack_channel": None,
            "slack_username": None,
            "slack_icon_emoji": None,
            "slack_route_urls": {},
            "allowed_hosts": "Hooks.Example.com, hooks.slack.com ",
            "allow_private_targets": False,
            "require_https": True,
        }
    )

    assert settings.webhook.allowed_hosts == ["hooks.example.com", "hooks.slack.com"]


def test_event_specific_retry_policy_overrides_are_loaded():
    settings = build_settings(
        external_event_policies={
            "email_send_password_reset": {
                "timeout_seconds": 3.0,
                "max_attempts": 5,
                "backoff_seconds": 1.0,
                "max_backoff_seconds": 8.0,
                "retry_on_statuses": "[408,429,500]",
            }
        }
    )

    policy = settings.external_event_policies.email_send_password_reset

    assert policy is not None
    assert policy.timeout_seconds == 3.0
    assert policy.max_attempts == 5
    assert policy.retry_on_statuses == [408, 429, 500]


def test_production_worker_requires_broker_url():
    with pytest.raises(ValidationError) as exc_info:
        build_settings(
            app={"name": "FastAPI Template", "debug": False, "env": "production"},
            api={
                "v1_prefix": "/api/v1",
                "cors_origins": ["https://app.example.com"],
            },
            worker={
                "enabled": True,
                "broker_url": None,
                "queue_name": "app.default",
                "retry_queue_name": "app.default.retry",
                "dead_letter_queue_name": "app.default.dlq",
                "prefetch_count": 10,
                "max_retries": 3,
                "retry_delay_ms": 30000,
                "max_retry_delay_ms": 300000,
                "requeue_on_failure": False,
                "idempotency_enabled": True,
                "idempotency_backend": "memory",
                "idempotency_redis_url": None,
                "idempotency_key_prefix": "worker_idempotency",
                "idempotency_ttl_seconds": 86400,
            },
        )

    assert "WORKER__BROKER_URL must be configured when WORKER__ENABLED=true." in str(
        exc_info.value
    )


def test_production_worker_redis_idempotency_requires_redis_url():
    with pytest.raises(ValidationError) as exc_info:
        build_settings(
            app={"name": "FastAPI Template", "debug": False, "env": "production"},
            api={
                "v1_prefix": "/api/v1",
                "cors_origins": ["https://app.example.com"],
            },
            worker={
                "enabled": True,
                "broker_url": "amqp://guest:guest@queue:5672/",
                "queue_name": "app.default",
                "retry_queue_name": "app.default.retry",
                "dead_letter_queue_name": "app.default.dlq",
                "prefetch_count": 10,
                "max_retries": 3,
                "retry_delay_ms": 30000,
                "max_retry_delay_ms": 300000,
                "requeue_on_failure": False,
                "idempotency_enabled": True,
                "idempotency_backend": "redis",
                "idempotency_redis_url": None,
                "idempotency_key_prefix": "worker_idempotency",
                "idempotency_ttl_seconds": 86400,
            },
        )

    assert "WORKER__IDEMPOTENCY_REDIS_URL must be configured" in str(exc_info.value)


def test_external_retry_statuses_parse_from_string():
    settings = build_settings(
        external={
            "timeout_seconds": 10.0,
            "max_attempts": 3,
            "backoff_seconds": 0.5,
            "max_backoff_seconds": 5.0,
            "retry_on_statuses": "429,500,503",
        }
    )

    assert settings.external.retry_on_statuses == [429, 500, 503]


def test_provider_specific_retry_policy_overrides_are_loaded():
    settings = build_settings(
        external_policies={
            "smtp": {
                "timeout_seconds": 20.0,
                "max_attempts": 5,
                "backoff_seconds": 1.0,
                "max_backoff_seconds": 8.0,
                "retry_on_statuses": [500, 503],
            }
        }
    )

    assert settings.external_policies.smtp.timeout_seconds == 20.0
    assert settings.external_policies.smtp.max_attempts == 5
    assert settings.external_policies.smtp.retry_on_statuses == [500, 503]
