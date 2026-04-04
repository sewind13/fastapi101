from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.db.models.feature_entitlement import FeatureEntitlement
from app.db.repositories.exceptions import RepositoryError


def get_active_entitlement_for_update(
    session: Session,
    *,
    account_id: int,
    resource_key: str,
) -> FeatureEntitlement | None:
    now = datetime.now(UTC)
    valid_from = cast(Any, FeatureEntitlement.valid_from)
    valid_until = cast(Any, FeatureEntitlement.valid_until)
    statement = (
        select(FeatureEntitlement)
        .where(FeatureEntitlement.account_id == account_id)
        .where(FeatureEntitlement.resource_key == resource_key)
        .where(FeatureEntitlement.status == "active")
        .where((col(valid_from).is_(None)) | (valid_from <= now))
        .where(
            (col(valid_until).is_(None))
            | (valid_until >= now)
        )
        .order_by(col(FeatureEntitlement.id).desc())
        .with_for_update()
    )
    return session.exec(statement).first()


def create_feature_entitlement(
    session: Session,
    entitlement: FeatureEntitlement,
) -> FeatureEntitlement:
    try:
        session.add(entitlement)
        session.commit()
        session.refresh(entitlement)
        return entitlement
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to persist entitlement") from exc


def list_account_entitlements(session: Session, *, account_id: int) -> list[FeatureEntitlement]:
    statement = (
        select(FeatureEntitlement)
        .where(FeatureEntitlement.account_id == account_id)
        .order_by(col(FeatureEntitlement.id).desc())
    )
    return list(session.exec(statement).all())


def update_entitlement_usage(
    session: Session,
    *,
    entitlement: FeatureEntitlement,
    units_delta: int,
) -> FeatureEntitlement:
    try:
        entitlement.units_used += units_delta
        entitlement.updated_at = datetime.now(UTC)
        session.add(entitlement)
        session.flush()
        return entitlement
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to update entitlement usage") from exc


def sum_remaining_units(
    session: Session,
    *,
    account_id: int,
    resource_key: str,
) -> int:
    now = datetime.now(UTC)
    valid_from = cast(Any, FeatureEntitlement.valid_from)
    valid_until = cast(Any, FeatureEntitlement.valid_until)
    statement = (
        select(
            func.coalesce(
                func.sum(FeatureEntitlement.units_total - FeatureEntitlement.units_used),
                0,
            )
        )
        .where(FeatureEntitlement.account_id == account_id)
        .where(FeatureEntitlement.resource_key == resource_key)
        .where(FeatureEntitlement.status == "active")
        .where((col(valid_from).is_(None)) | (valid_from <= now))
        .where(
            (col(valid_until).is_(None))
            | (valid_until >= now)
        )
    )
    result = session.exec(statement).one()
    return int(result or 0)
