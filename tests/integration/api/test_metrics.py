import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health_response = await client.get("/health/live")
        metrics_response = await client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers["content-type"]
    body = metrics_response.text
    assert "fastapi_template_http_requests_total" in body
    assert 'path="/health/live"' in body
    assert 'status_code="200"' in body
    assert "fastapi_template_http_request_duration_seconds" in body
    assert "fastapi_template_http_requests_in_progress" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_include_exception_and_readiness_dependency_series(monkeypatch):
    from app.core import health
    from app.services.result import ServiceError, ServiceResult

    monkeypatch.setattr(
        health,
        "check_db_connection",
        lambda: (_ for _ in ()).throw(RuntimeError("db down")),
    )
    monkeypatch.setattr(health.settings.health, "enable_redis_check", True)
    monkeypatch.setattr(health.settings.health, "enable_s3_check", False)
    monkeypatch.setattr(health.settings.health, "enable_queue_check", False)
    monkeypatch.setattr(
        health,
        "_redis_check",
        lambda: health.CheckResult(name="redis", status="ok"),
    )
    monkeypatch.setattr("app.main.run_readiness_checks", health.run_readiness_checks)
    monkeypatch.setattr(
        "app.api.v1.auth.authenticate_user",
        lambda session, username, password: ServiceResult(
            error=ServiceError(
                code="auth.invalid_credentials",
                message="Invalid username or password.",
            )
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        readiness_response = await client.get("/health/ready")
        missing_response = await client.get("/missing-route")
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": "unknown-user", "password": "bad-password"},
        )
        metrics_response = await client.get("/metrics")

    assert readiness_response.status_code == 503
    assert missing_response.status_code == 404
    assert login_response.status_code == 401
    assert metrics_response.status_code == 200
    body = metrics_response.text
    assert "fastapi_template_app_exceptions_total" in body
    assert 'error_code="404"' in body
    assert "fastapi_template_readiness_checks_total" in body
    assert 'dependency="database",status="failed"' in body
    assert "fastapi_template_readiness_dependency_status" in body
    assert "fastapi_template_auth_events_total" in body
    assert 'event="login",outcome="failed"' in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_include_cache_series(monkeypatch):
    from app.core import cache

    monkeypatch.setattr(cache.settings.cache, "enabled", True)
    monkeypatch.setattr(cache.settings.cache, "backend", "memory")
    cache.memory_cache.clear()

    cache.get_json("missing-key", cache_name="items_list")
    cache.set_json("items-key", [{"id": 1}], cache_name="items_list", ttl_seconds=60)
    cache.get_json("items-key", cache_name="items_list")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        metrics_response = await client.get("/metrics")

    assert metrics_response.status_code == 200
    body = metrics_response.text
    assert "fastapi_template_cache_operations_total" in body
    assert 'cache_name="items_list"' in body
    assert 'backend="memory"' in body
    assert 'operation="get",outcome="miss"' in body or 'outcome="miss",operation="get"' in body
    assert 'operation="set",outcome="stored"' in body or 'outcome="stored",operation="set"' in body
    assert 'operation="get",outcome="hit"' in body or 'outcome="hit",operation="get"' in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint_requires_bearer_token_when_configured(monkeypatch):
    monkeypatch.setattr("app.main.settings.metrics.auth_token", "metrics-secret")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        unauthorized = await client.get("/metrics")
        authorized = await client.get(
            "/metrics",
            headers={"Authorization": "Bearer metrics-secret"},
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
