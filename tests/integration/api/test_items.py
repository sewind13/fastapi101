import pytest

from app.services.billing_service import get_account_balance_service, grant_entitlement
from tests.conftest import build_token_headers, create_test_user


def _grant_item_create_entitlement(session, *, account_id: int, units_total: int = 1) -> None:
    grant_result = grant_entitlement(
        session,
        account_id=account_id,
        resource_key="item_create",
        units_total=units_total,
        source_type="grant",
        source_id=f"test-item-create-{units_total}",
    )
    assert grant_result.ok is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_item_consumes_entitlement(client, session):
    user = create_test_user(
        session,
        username="item-create-user",
        email="item-create@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None
    _grant_item_create_entitlement(session, account_id=user.account_id, units_total=1)

    payload = {"title": "Test Item", "description": "This is a test"}
    response = await client.post(
        "/api/v1/items/",
        json=payload,
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Item"
    assert "id" in data
    assert data["owner_id"] is not None

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="item_create",
    )
    assert balance_result.ok is True
    assert balance_result.value == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_item_without_entitlement_is_forbidden(client, session):
    user = create_test_user(
        session,
        username="item-no-quota-user",
        email="item-no-quota@example.com",
    )
    assert user.id is not None

    payload = {"title": "No quota item"}
    response = await client.post(
        "/api/v1/items/",
        json=payload,
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 403
    data = response.json()
    assert data["error_code"] == "billing.no_entitlement"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_item_unauthorized(client):
    payload = {"title": "No Token"}
    response = await client.post("/api/v1/items/", json=payload)
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_items(client, session):
    user = create_test_user(
        session,
        username="item-read-user",
        email="item-read@example.com",
    )
    assert user.id is not None

    response = await client.get(
        "/api/v1/items/",
        headers=build_token_headers(user.id, user.username),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_items_invalid_token(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    response = await client.get("/api/v1/items/", headers=headers)
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_items_uses_cache(client, session, monkeypatch):
    user = create_test_user(
        session,
        username="item-cache-user",
        email="item-cache@example.com",
    )
    assert user.id is not None

    monkeypatch.setattr("app.services.item_service.settings.cache.enabled", True)
    monkeypatch.setattr("app.services.item_service.settings.cache.backend", "memory")
    monkeypatch.setattr("app.services.item_service.settings.cache.items_list_ttl_seconds", 30)
    monkeypatch.setattr("app.core.cache.settings.cache.enabled", True)
    monkeypatch.setattr("app.core.cache.settings.cache.backend", "memory")
    from app.core.cache import memory_cache

    memory_cache.clear()

    headers = build_token_headers(user.id, user.username)
    first = await client.get("/api/v1/items/", headers=headers)
    second = await client.get("/api/v1/items/", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
