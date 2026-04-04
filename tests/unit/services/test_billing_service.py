from app.services.billing_service import (
    get_account_balance_service,
    grant_entitlement,
    list_account_entitlements_service,
)
from app.services.entitlement_service import (
    commit_reserved_usage,
    release_reserved_usage,
    reserve_feature_usage,
)
from tests.conftest import create_test_user


def test_grant_entitlement_and_get_balance(session):
    user = create_test_user(
        session,
        username="billing-user",
        email="billing@example.com",
    )
    assert user.account_id is not None

    grant_result = grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="service_a",
        units_total=30,
        source_type="grant",
        source_id="grant-1",
    )

    assert grant_result.ok is True
    assert grant_result.value is not None

    list_result = list_account_entitlements_service(session, account_id=user.account_id)
    assert list_result.ok is True
    assert list_result.value is not None
    assert len(list_result.value) == 1

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="service_a",
    )
    assert balance_result.ok is True
    assert balance_result.value == 30


def test_reserve_and_commit_usage_consumes_balance(session):
    user = create_test_user(
        session,
        username="commit-user",
        email="commit@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="service_a",
        units_total=2,
        source_type="grant",
        source_id="grant-2",
    )

    reservation_result = reserve_feature_usage(
        session,
        account_id=user.account_id,
        feature_key="service_a.run",
        user_id=user.id,
        request_id="req-commit",
    )

    assert reservation_result.ok is True
    assert reservation_result.value is not None

    commit_result = commit_reserved_usage(
        session,
        reservation_id=reservation_result.value.id or 0,
    )

    assert commit_result.ok is True
    assert commit_result.value is not None

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="service_a",
    )
    assert balance_result.ok is True
    assert balance_result.value == 1


def test_release_reserved_usage_keeps_balance_unchanged(session):
    user = create_test_user(
        session,
        username="release-user",
        email="release@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="service_a",
        units_total=3,
        source_type="grant",
        source_id="grant-3",
    )

    reservation_result = reserve_feature_usage(
        session,
        account_id=user.account_id,
        feature_key="service_a.run",
        user_id=user.id,
        request_id="req-release",
    )

    assert reservation_result.ok is True
    assert reservation_result.value is not None

    release_result = release_reserved_usage(
        session,
        reservation_id=reservation_result.value.id or 0,
    )

    assert release_result.ok is True

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="service_a",
    )
    assert balance_result.ok is True
    assert balance_result.value == 3


def test_items_create_policy_consumes_item_create_entitlement(session):
    user = create_test_user(
        session,
        username="items-policy-user",
        email="items-policy@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_create",
        units_total=1,
        source_type="grant",
        source_id="grant-items-1",
    )

    reservation_result = reserve_feature_usage(
        session,
        account_id=user.account_id,
        feature_key="items.create",
        user_id=user.id,
        request_id="req-items-create",
    )

    assert reservation_result.ok is True
    assert reservation_result.value is not None

    commit_result = commit_reserved_usage(
        session,
        reservation_id=reservation_result.value.id or 0,
    )

    assert commit_result.ok is True

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="item_create",
    )
    assert balance_result.ok is True
    assert balance_result.value == 0
