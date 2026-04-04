import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import DependencyCheckResponse, ReadinessResponse


@pytest.mark.asyncio
async def test_sampling_skips_success_logs_when_sample_rate_is_zero(monkeypatch):
    entries = []

    monkeypatch.setattr("app.main.random", lambda: 0.9)
    monkeypatch.setattr("app.main.settings.logging.access_log_sample_rate", 0.0)
    monkeypatch.setattr("app.main.settings.logging.access_log_skip_paths", [])
    monkeypatch.setattr("app.main.settings.logging.access_log_skip_prefixes", [])
    monkeypatch.setattr(
        "app.main.logger.info",
        lambda message, extra=None: entries.append((message, extra)),
    )
    monkeypatch.setattr(
        "app.main.run_readiness_checks",
        lambda: ReadinessResponse(
            status="ok",
            checks=[
                DependencyCheckResponse(name="database", status="ok"),
                DependencyCheckResponse(
                    name="redis",
                    status="skipped",
                    message="Check disabled.",
                ),
                DependencyCheckResponse(
                    name="s3",
                    status="skipped",
                    message="Check disabled.",
                ),
                DependencyCheckResponse(
                    name="queue",
                    status="skipped",
                    message="Check disabled.",
                ),
            ],
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert entries == []


@pytest.mark.asyncio
async def test_sampling_always_logs_error_responses(monkeypatch):
    entries = []

    monkeypatch.setattr("app.main.random", lambda: 0.9)
    monkeypatch.setattr("app.main.settings.logging.access_log_sample_rate", 0.0)
    monkeypatch.setattr("app.main.settings.logging.access_log_skip_paths", [])
    monkeypatch.setattr("app.main.settings.logging.access_log_skip_prefixes", [])
    monkeypatch.setattr(
        "app.main.logger.info",
        lambda message, extra=None: entries.append((message, extra)),
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/missing-route")

    assert response.status_code == 404
    assert len(entries) == 1
    message, extra = entries[0]
    assert message == "request completed"
    assert extra["status_code"] == 404
    assert "response_size_bytes" in extra
