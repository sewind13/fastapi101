from typing import Any

from app.core.settings.constants import DEFAULT_AUDIENCE, DEFAULT_ISSUER, DEFAULT_SECRET_KEY


def validate_production_settings(settings: Any) -> Any:
    env = settings.app.env.lower().strip()
    is_local_like = env in {"development", "dev", "local", "testing", "test"}

    if (
        settings.security.secret_key == DEFAULT_SECRET_KEY
        and not is_local_like
        and env != "production"
    ):
        raise ValueError(
            "SECURITY__SECRET_KEY must be replaced before deploying to non-local environments."
        )

    if env != "production":
        return settings

    errors: list[str] = []

    if settings.app.debug:
        errors.append("APP__DEBUG must be false in production.")

    if settings.security.secret_key == DEFAULT_SECRET_KEY or len(settings.security.secret_key) < 32:
        errors.append(
            "SECURITY__SECRET_KEY must be replaced with a strong secret "
            "that is at least 32 characters long."
        )

    if settings.security.issuer == DEFAULT_ISSUER:
        errors.append("SECURITY__ISSUER must be set to a production-specific value.")

    if settings.security.audience == DEFAULT_AUDIENCE:
        errors.append("SECURITY__AUDIENCE must be set to a production-specific value.")

    if settings.security.email_verification_enabled and not settings.app.public_base_url:
        errors.append(
            "APP__PUBLIC_BASE_URL must be configured when "
            "SECURITY__EMAIL_VERIFICATION_ENABLED=true."
        )

    if settings.database.url.startswith("sqlite"):
        errors.append("DATABASE__URL must point to a production database and cannot use SQLite.")

    if not settings.api.cors_origins:
        errors.append("API__CORS_ORIGINS must be explicitly configured in production.")

    if settings.auth_rate_limit.enabled:
        if settings.auth_rate_limit.backend != "redis":
            errors.append(
                "AUTH_RATE_LIMIT__BACKEND must be 'redis' in production "
                "to support multi-instance deployments."
            )
        if not settings.auth_rate_limit.redis_url:
            errors.append(
                "AUTH_RATE_LIMIT__REDIS_URL must be configured when "
                "production rate limiting is enabled."
            )

    if (
        settings.cache.enabled
        and settings.cache.backend == "redis"
        and not settings.cache.redis_url
    ):
        errors.append(
            "CACHE__REDIS_URL must be configured when CACHE__ENABLED=true "
            "and CACHE__BACKEND='redis'."
        )

    if settings.metrics.enabled and not settings.metrics.auth_token:
        errors.append(
            "METRICS__AUTH_TOKEN must be configured when METRICS__ENABLED=true in production."
        )

    if settings.webhook.enabled and not settings.webhook.dry_run:
        if settings.webhook.provider == "generic" and not settings.webhook.allowed_hosts:
            errors.append(
                "WEBHOOK__ALLOWED_HOSTS must be configured when WEBHOOK__ENABLED=true, "
                "WEBHOOK__DRY_RUN=false, and WEBHOOK__PROVIDER='generic' in production."
            )

    if settings.api.public_registration_enabled and settings.ops.enabled:
        errors.append(
            "API__PUBLIC_REGISTRATION_ENABLED should be false in production when "
            "operations endpoints are enabled."
        )

    if settings.worker.enabled and not settings.worker.broker_url:
        errors.append("WORKER__BROKER_URL must be configured when WORKER__ENABLED=true.")

    if (
        settings.worker.enabled
        and settings.worker.idempotency_enabled
        and settings.worker.idempotency_backend == "redis"
        and not settings.worker.idempotency_redis_url
    ):
        errors.append(
            "WORKER__IDEMPOTENCY_REDIS_URL must be configured when "
            "WORKER__IDEMPOTENCY_ENABLED=true and WORKER__IDEMPOTENCY_BACKEND='redis'."
        )

    if errors:
        raise ValueError(" ".join(errors))

    return settings
