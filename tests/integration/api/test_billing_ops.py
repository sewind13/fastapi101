from datetime import UTC, datetime, timedelta

import pytest

from app.db.models.usage_event import UsageEvent
from tests.conftest import build_token_headers, create_test_user


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_can_grant_and_list_entitlements(client, session):
    admin = create_test_user(
        session,
        username="billingopsadmin",
        email="billingopsadmin@example.com",
        role="ops_admin",
    )
    target_user = create_test_user(
        session,
        username="billingtarget",
        email="billingtarget@example.com",
    )
    assert admin.id is not None
    assert target_user.account_id is not None

    grant_response = await client.post(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/grant",
        headers=build_token_headers(admin.id, admin.username),
        json={
            "resource_key": "service_a",
            "units_total": 30,
            "source_type": "grant",
            "source_id": "grant-api-1",
        },
    )

    assert grant_response.status_code == 200
    assert grant_response.json()["units_remaining"] == 30

    list_response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/entitlements",
        headers=build_token_headers(admin.id, admin.username),
    )

    assert list_response.status_code == 200
    data = list_response.json()
    assert data["account_id"] == target_user.account_id
    assert len(data["entitlements"]) == 1
    assert data["entitlements"][0]["resource_key"] == "service_a"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_billing_balance_and_usage_endpoints(client, session):
    admin = create_test_user(
        session,
        username="billingopsadmin2",
        email="billingopsadmin2@example.com",
        role="ops_admin",
    )
    target_user = create_test_user(
        session,
        username="billingtarget2",
        email="billingtarget2@example.com",
    )
    assert admin.id is not None
    assert target_user.account_id is not None

    await client.post(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/grant",
        headers=build_token_headers(admin.id, admin.username),
        json={
            "resource_key": "service_a",
            "units_total": 5,
            "source_type": "grant",
            "source_id": "grant-api-2",
        },
    )

    session.add(
        UsageEvent(
            account_id=target_user.account_id,
            entitlement_id=1,
            reservation_id=None,
            user_id=target_user.id,
            resource_key="service_a",
            feature_key="service_a.run",
            units=1,
            request_id="usage-1",
            status="committed",
        )
    )
    session.commit()

    balance_response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/balance/service_a",
        headers=build_token_headers(admin.id, admin.username),
    )
    assert balance_response.status_code == 200
    assert balance_response.json()["units_remaining"] == 5

    usage_response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/usage",
        headers=build_token_headers(admin.id, admin.username),
    )
    assert usage_response.status_code == 200
    usage_data = usage_response.json()
    assert usage_data["account_id"] == target_user.account_id
    assert usage_data["total_count"] == 1
    assert usage_data["has_next"] is False
    assert usage_data["has_prev"] is False
    assert len(usage_data["usage_events"]) == 1
    assert usage_data["usage_events"][0]["feature_key"] == "service_a.run"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_can_filter_usage_by_time_and_sort(client, session):
    admin = create_test_user(
        session,
        username="billingopsadmin3",
        email="billingopsadmin3@example.com",
        role="ops_admin",
    )
    target_user = create_test_user(
        session,
        username="billingtarget3",
        email="billingtarget3@example.com",
    )
    assert admin.id is not None
    assert target_user.account_id is not None

    grant_response = await client.post(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/grant",
        headers=build_token_headers(admin.id, admin.username),
        json={
            "resource_key": "service_a",
            "units_total": 5,
            "source_type": "grant",
            "source_id": "grant-api-3",
        },
    )
    assert grant_response.status_code == 200
    entitlement_id = grant_response.json()["id"]
    now = datetime.now(UTC)

    session.add_all(
        [
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-time-1",
                status="committed",
                created_at=now - timedelta(days=2),
            ),
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-time-2",
                status="committed",
                created_at=now - timedelta(days=1),
            ),
        ]
    )
    session.commit()

    usage_response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/usage",
        params={
            "sort": "asc",
            "created_after": (now - timedelta(days=3)).isoformat(),
            "resource_key": "service_a",
        },
        headers=build_token_headers(admin.id, admin.username),
    )
    assert usage_response.status_code == 200
    usage_data = usage_response.json()
    assert usage_data["total_count"] == 2
    assert usage_data["usage_events"][0]["request_id"] == "ops-time-1"
    assert usage_data["usage_events"][1]["request_id"] == "ops-time-2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_can_filter_usage_by_status(client, session):
    admin = create_test_user(
        session,
        username="billingopsadmin4",
        email="billingopsadmin4@example.com",
        role="ops_admin",
    )
    target_user = create_test_user(
        session,
        username="billingtarget4",
        email="billingtarget4@example.com",
    )
    assert admin.id is not None
    assert target_user.account_id is not None

    grant_response = await client.post(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/grant",
        headers=build_token_headers(admin.id, admin.username),
        json={
            "resource_key": "service_a",
            "units_total": 5,
            "source_type": "grant",
            "source_id": "grant-api-4",
        },
    )
    assert grant_response.status_code == 200
    entitlement_id = grant_response.json()["id"]

    session.add_all(
        [
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-status-1",
                status="committed",
            ),
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-status-2",
                status="reversed",
            ),
        ]
    )
    session.commit()

    usage_response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/usage",
        params={"status": "reversed"},
        headers=build_token_headers(admin.id, admin.username),
    )
    assert usage_response.status_code == 200
    usage_data = usage_response.json()
    assert usage_data["total_count"] == 1
    assert len(usage_data["usage_events"]) == 1
    assert usage_data["usage_events"][0]["status"] == "reversed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ops_can_read_usage_report(client, session):
    admin = create_test_user(
        session,
        username="billingopsadmin5",
        email="billingopsadmin5@example.com",
        role="ops_admin",
    )
    target_user = create_test_user(
        session,
        username="billingtarget5",
        email="billingtarget5@example.com",
    )
    assert admin.id is not None
    assert target_user.account_id is not None

    grant_response = await client.post(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/grant",
        headers=build_token_headers(admin.id, admin.username),
        json={
            "resource_key": "service_a",
            "units_total": 5,
            "source_type": "grant",
            "source_id": "grant-api-5",
        },
    )
    assert grant_response.status_code == 200
    entitlement_id = grant_response.json()["id"]

    session.add_all(
        [
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-report-1",
                status="committed",
            ),
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=3,
                request_id="ops-report-2",
                status="committed",
            ),
            UsageEvent(
                account_id=target_user.account_id,
                entitlement_id=entitlement_id,
                reservation_id=None,
                user_id=target_user.id,
                resource_key="service_a",
                feature_key="service_a.run",
                units=1,
                request_id="ops-report-3",
                status="reversed",
            ),
        ]
    )
    session.commit()

    response = await client.get(
        f"/api/v1/ops/billing/accounts/{target_user.account_id}/usage/report",
        params={"resource_key": "service_a"},
        headers=build_token_headers(admin.id, admin.username),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == target_user.account_id
    assert len(data["aggregates"]) == 2
    assert all(item["resource_key"] == "service_a" for item in data["aggregates"])
