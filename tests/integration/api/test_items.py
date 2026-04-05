import pytest

from app.db.models.item import Item
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


def _grant_item_archive_entitlement(session, *, account_id: int, units_total: int = 1) -> None:
    grant_result = grant_entitlement(
        session,
        account_id=account_id,
        resource_key="item_archive",
        units_total=units_total,
        source_type="grant",
        source_id=f"test-item-archive-{units_total}",
    )
    assert grant_result.ok is True


def _create_item(session, *, owner_id: int, title: str = "Existing Item") -> Item:
    item = Item(
        title=title,
        description="seeded for integration test",
        owner_id=owner_id,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_item_success(client, session):
    user = create_test_user(
        session,
        username="item-archive-user",
        email="item-archive@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None
    _grant_item_archive_entitlement(session, account_id=user.account_id, units_total=1)
    item = _create_item(session, owner_id=user.id, title="Archive Me")

    response = await client.post(
        f"/api/v1/items/{item.id}/archive",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item.id
    assert data["is_archived"] is True
    assert data["archived_at"] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_item_without_entitlement_is_forbidden(client, session):
    user = create_test_user(
        session,
        username="item-archive-no-quota-user",
        email="item-archive-no-quota@example.com",
    )
    assert user.id is not None
    item = _create_item(session, owner_id=user.id, title="Archive No Quota")

    response = await client.post(
        f"/api/v1/items/{item.id}/archive",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "billing.no_entitlement"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_item_forbidden_for_non_owner(client, session):
    owner = create_test_user(
        session,
        username="item-owner-user",
        email="item-owner@example.com",
    )
    attacker = create_test_user(
        session,
        username="item-attacker-user",
        email="item-attacker@example.com",
    )
    assert owner.id is not None
    assert attacker.id is not None
    item = _create_item(session, owner_id=owner.id, title="Private Item")

    response = await client.post(
        f"/api/v1/items/{item.id}/archive",
        headers=build_token_headers(attacker.id, attacker.username),
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "item.forbidden"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_item_not_found(client, session):
    user = create_test_user(
        session,
        username="item-missing-user",
        email="item-missing@example.com",
    )
    assert user.id is not None

    response = await client.post(
        "/api/v1/items/999999/archive",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "item.not_found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_item_already_archived(client, session):
    user = create_test_user(
        session,
        username="item-already-archived-user",
        email="item-already-archived@example.com",
    )
    assert user.id is not None
    item = _create_item(session, owner_id=user.id, title="Already Archived")
    item.is_archived = True
    session.add(item)
    session.commit()

    response = await client.post(
        f"/api/v1/items/{item.id}/archive",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "item.already_archived"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_items_hides_archived_items_by_default(client, session):
    user = create_test_user(
        session,
        username="item-hidden-archive-user",
        email="item-hidden-archive@example.com",
    )
    assert user.id is not None
    active_item = _create_item(session, owner_id=user.id, title="Visible Item")
    archived_item = _create_item(session, owner_id=user.id, title="Hidden Item")
    archived_item.is_archived = True
    session.add(archived_item)
    session.commit()

    response = await client.get(
        "/api/v1/items/",
        headers=build_token_headers(user.id, user.username),
    )

    assert response.status_code == 200
    data = response.json()
    returned_ids = {item["id"] for item in data}
    assert active_item.id in returned_ids
    assert archived_item.id not in returned_ids
