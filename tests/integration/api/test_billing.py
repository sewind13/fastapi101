from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.usage_event import UsageEvent
from app.services.billing_service import grant_entitlement
from tests.conftest import build_token_headers, create_test_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_read_own_entitlements_and_balance(client, session):
    user = create_test_user(
        session,
        username="selfbillinguser",
        email="selfbilling@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=3,
        source_type="grant",
        source_id="self-grant-1",
    )
    assert grant_result.ok is True

    entitlements_response = await client.get(
        "/api/v1/billing/me/entitlements",
        headers=build_token_headers(user.id, user.username),
    )
    assert entitlements_response.status_code == 200
    entitlements_data = entitlements_response.json()
    assert entitlements_data["account_id"] == user.account_id
    assert len(entitlements_data["entitlements"]) == 1
    assert entitlements_data["entitlements"][0]["resource_key"] == "item_create"

    balance_response = await client.get(
        "/api/v1/billing/me/balance/item_create",
        headers=build_token_headers(user.id, user.username),
    )
    assert balance_response.status_code == 200
    assert balance_response.json()["units_remaining"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_read_own_usage_events(client, session):
    user = create_test_user(
        session,
        username="selfusageuser",
        email="selfusage@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=2,
        source_type="grant",
        source_id="self-grant-2",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    session.add(
        UsageEvent(
            account_id=user.account_id,
            entitlement_id=grant_result.value.id or 0,
            reservation_id=None,
            user_id=user.id,
            resource_key="item_create",
            feature_key="items.create",
            units=1,
            request_id="self-usage-1",
            status="committed",
        )
    )
    session.commit()

    usage_response = await client.get(
        "/api/v1/billing/me/usage",
        headers=build_token_headers(user.id, user.username),
    )
    assert usage_response.status_code == 200
    usage_data = usage_response.json()
    assert usage_data["account_id"] == user.account_id
    assert usage_data["total_count"] == 1
    assert usage_data["has_next"] is False
    assert usage_data["has_prev"] is False
    assert len(usage_data["usage_events"]) == 1
    assert usage_data["usage_events"][0]["feature_key"] == "items.create"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_read_billing_summary(client, session):
    user = create_test_user(
        session,
        username="selfsummaryuser",
        email="selfsummary@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=4,
        source_type="grant",
        source_id="self-grant-3",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    session.add(
        UsageEvent(
            account_id=user.account_id,
            entitlement_id=grant_result.value.id or 0,
            reservation_id=None,
            user_id=user.id,
            resource_key="item_create",
            feature_key="items.create",
            units=1,
            request_id="self-summary-1",
            status="committed",
        )
    )
    session.commit()

    response = await client.get(
        "/api/v1/billing/me/summary",
        headers=build_token_headers(user.id, user.username),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == user.account_id
    assert len(data["entitlements"]) == 1
    assert len(data["balances"]) == 1
    assert data["balances"][0]["resource_key"] == "item_create"
    assert data["balances"][0]["units_remaining"] == 4
    assert len(data["recent_usage_events"]) == 1
    assert data["recent_usage_events"][0]["feature_key"] == "items.create"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_filter_and_paginate_usage_events(client, session):
    user = create_test_user(
        session,
        username="selfusagefilteruser",
        email="selfusagefilter@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=5,
        source_type="grant",
        source_id="self-grant-4",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    session.add_all(
        [
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-filter-1",
                status="committed",
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-filter-2",
                status="committed",
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.import",
                units=1,
                request_id="self-filter-3",
                status="committed",
            ),
        ]
    )
    session.commit()

    filtered_response = await client.get(
        "/api/v1/billing/me/usage?feature_key=items.create&limit=1&offset=0",
        headers=build_token_headers(user.id, user.username),
    )
    assert filtered_response.status_code == 200
    filtered_data = filtered_response.json()
    assert filtered_data["account_id"] == user.account_id
    assert filtered_data["total_count"] == 2
    assert filtered_data["has_next"] is True
    assert filtered_data["has_prev"] is False
    assert len(filtered_data["usage_events"]) == 1
    assert filtered_data["usage_events"][0]["feature_key"] == "items.create"

    next_page_response = await client.get(
        "/api/v1/billing/me/usage?resource_key=item_create&limit=1&offset=1",
        headers=build_token_headers(user.id, user.username),
    )
    assert next_page_response.status_code == 200
    next_page_data = next_page_response.json()
    assert next_page_data["total_count"] == 3
    assert next_page_data["has_next"] is True
    assert next_page_data["has_prev"] is True
    assert len(next_page_data["usage_events"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_sort_and_filter_usage_by_created_at(client, session):
    user = create_test_user(
        session,
        username="selfusagetimelineuser",
        email="selfusagetimeline@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=5,
        source_type="grant",
        source_id="self-grant-5",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    now = datetime.now(UTC)
    session.add_all(
        [
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-time-1",
                status="committed",
                created_at=now - timedelta(days=2),
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-time-2",
                status="committed",
                created_at=now - timedelta(days=1),
            ),
        ]
    )
    session.commit()

    asc_response = await client.get(
        "/api/v1/billing/me/usage",
        params={
            "sort": "asc",
            "created_after": (now - timedelta(days=3)).isoformat(),
            "created_before": now.isoformat(),
        },
        headers=build_token_headers(user.id, user.username),
    )
    assert asc_response.status_code == 200
    asc_data = asc_response.json()
    assert asc_data["total_count"] == 2
    assert asc_data["usage_events"][0]["request_id"] == "self-time-1"
    assert asc_data["usage_events"][1]["request_id"] == "self-time-2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_filter_usage_by_status(client, session):
    user = create_test_user(
        session,
        username="selfusagestatususer",
        email="selfusagestatus@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=5,
        source_type="grant",
        source_id="self-grant-6",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    session.add_all(
        [
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-status-1",
                status="committed",
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-status-2",
                status="reversed",
            ),
        ]
    )
    session.commit()

    response = await client.get(
        "/api/v1/billing/me/usage",
        params={"status": "reversed"},
        headers=build_token_headers(user.id, user.username),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert len(data["usage_events"]) == 1
    assert data["usage_events"][0]["status"] == "reversed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_can_read_usage_report(client, session):
    user = create_test_user(
        session,
        username="selfusagereportuser",
        email="selfusagereport@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=5,
        source_type="grant",
        source_id="self-grant-7",
    )
    assert grant_result.ok is True
    assert grant_result.value is not None

    session.add_all(
        [
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-report-1",
                status="committed",
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=2,
                request_id="self-report-2",
                status="committed",
            ),
            UsageEvent(
                account_id=user.account_id,
                entitlement_id=grant_result.value.id or 0,
                reservation_id=None,
                user_id=user.id,
                resource_key="item_create",
                feature_key="items.create",
                units=1,
                request_id="self-report-3",
                status="reversed",
            ),
        ]
    )
    session.commit()

    response = await client.get(
        "/api/v1/billing/me/usage/report",
        params={"feature_key": "items.create"},
        headers=build_token_headers(user.id, user.username),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == user.account_id
    assert len(data["aggregates"]) == 2
    assert data["aggregates"][0]["feature_key"] == "items.create"
