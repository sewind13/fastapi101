def promote_legacy_flat_env(data: object) -> object:
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
            "EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES": "email_verification_token_expire_minutes",
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
