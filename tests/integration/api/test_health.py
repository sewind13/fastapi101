import pytest

from app.schemas.common import DependencyCheckResponse, ReadinessResponse


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_check_returns_ok_when_db_is_available(client, monkeypatch):
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

    response = await client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"][0]["name"] == "database"
    assert body["checks"][0]["status"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_check_returns_503_when_db_is_unavailable(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.run_readiness_checks",
        lambda: ReadinessResponse(
            status="degraded",
            checks=[
                DependencyCheckResponse(
                    name="database",
                    status="failed",
                    message="db down",
                ),
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

    response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"][0]["name"] == "database"
    assert body["checks"][0]["status"] == "failed"
    assert body["checks"][0]["message"] == "db down"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_check_includes_optional_dependency_results(client, monkeypatch):
    monkeypatch.setattr(
        "app.main.run_readiness_checks",
        lambda: ReadinessResponse(
            status="degraded",
            checks=[
                DependencyCheckResponse(name="database", status="ok"),
                DependencyCheckResponse(name="redis", status="ok"),
                DependencyCheckResponse(
                    name="s3",
                    status="failed",
                    message="connection refused",
                ),
                DependencyCheckResponse(
                    name="queue",
                    status="skipped",
                    message="Check disabled.",
                ),
            ],
        ),
    )

    response = await client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    checks = {check["name"]: check for check in body["checks"]}
    assert checks["redis"]["status"] == "ok"
    assert checks["s3"]["status"] == "failed"
    assert checks["queue"]["status"] == "skipped"
