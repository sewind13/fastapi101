from datetime import UTC, datetime

from app.db.models.item import Item
from app.services.billing_service import get_account_balance_service, grant_entitlement
from app.services.exceptions import ErrorCode
from app.services.item_service import restore_item_for_user
from tests.conftest import create_test_user


def test_restore_item_for_user_restores_item_and_consumes_quota(session):
    user = create_test_user(
        session,
        username="restore-service-user",
        email="restore-service@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_restore",
        units_total=1,
        source_type="grant",
        source_id="grant-restore-service-1",
    )

    item = Item(
        title="Restore Service Item",
        description="archived item",
        owner_id=user.id,
        is_archived=True,
        archived_at=datetime.now(UTC),
        restore_count=0,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    result = restore_item_for_user(
        session=session,
        item_id=item.id or 0,
        current_user=user,
        request_id="req-restore-service-success",
    )

    assert result.ok is True
    assert result.value is not None
    assert result.value.is_archived is False
    assert result.value.archived_at is None
    assert result.value.restored_at is not None
    assert result.value.restore_count == 1

    refreshed = session.get(Item, item.id)
    assert refreshed is not None
    assert refreshed.is_archived is False
    assert refreshed.archived_at is None
    assert refreshed.restored_at is not None
    assert refreshed.restore_count == 1

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="item_restore",
    )
    assert balance_result.ok is True
    assert balance_result.value == 0


def test_restore_item_for_user_requires_archived_state_before_quota_check(session):
    user = create_test_user(
        session,
        username="restore-not-archived-user",
        email="restore-not-archived@example.com",
    )
    assert user.id is not None
    assert user.account_id is not None

    grant_entitlement(
        session,
        account_id=user.account_id,
        resource_key="item_restore",
        units_total=1,
        source_type="grant",
        source_id="grant-restore-service-2",
    )

    item = Item(
        title="Already Active",
        description="active item",
        owner_id=user.id,
        is_archived=False,
        restore_count=0,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    result = restore_item_for_user(
        session=session,
        item_id=item.id or 0,
        current_user=user,
        request_id="req-restore-service-not-archived",
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ErrorCode.ITEM_NOT_ARCHIVED

    balance_result = get_account_balance_service(
        session,
        account_id=user.account_id,
        resource_key="item_restore",
    )
    assert balance_result.ok is True
    assert balance_result.value == 1


def test_restore_item_for_user_without_entitlement_returns_billing_error(session):
    user = create_test_user(
        session,
        username="restore-no-entitlement-user",
        email="restore-no-entitlement@example.com",
    )
    assert user.id is not None

    item = Item(
        title="No Entitlement Restore",
        description="archived item",
        owner_id=user.id,
        is_archived=True,
        archived_at=datetime.now(UTC),
        restore_count=0,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    result = restore_item_for_user(
        session=session,
        item_id=item.id or 0,
        current_user=user,
        request_id="req-restore-service-no-entitlement",
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ErrorCode.BILLING_NO_ENTITLEMENT
