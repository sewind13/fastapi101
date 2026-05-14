import pytest
from httpx import ASGITransport, AsyncClient

from app.factory import create_app
from app.schemas.common import DependencyCheckResponse, ReadinessResponse


@pytest.mark.asyncio
async def test_create_app_registers_core_routes(monkeypatch):
    monkeypatch.setattr(
        "app.api.health.run_readiness_checks",
        lambda: ReadinessResponse(
            status="ok",
            checks=[DependencyCheckResponse(name="database", status="ok")],
        ),
    )

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health_response = await client.get("/health/live")
        readiness_response = await client.get("/health/ready")
        openapi_response = await client.get("/api/v1/openapi.json")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert readiness_response.status_code == 200
    assert readiness_response.json()["checks"][0]["name"] == "database"
    assert openapi_response.status_code == 200


@pytest.mark.asyncio
async def test_create_app_adds_request_id_header():
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"


@pytest.mark.asyncio
async def test_create_app_registers_validation_error_handler():
    app = create_app()

    @app.get("/contract/{item_id}")
    async def contract_route(item_id: int):
        return {"item_id": item_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/contract/not-an-int")

    body = response.json()
    assert response.status_code == 422
    assert body["error_code"] == "validation_error"
    assert body["path"] == "/contract/not-an-int"
    assert body["request_id"]
    assert body["details"]


@pytest.mark.asyncio
async def test_create_app_registers_metrics_endpoint():
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
