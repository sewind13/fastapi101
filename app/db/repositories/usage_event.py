from datetime import datetime
from typing import Any, TypedDict, cast

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.db.models.usage_event import UsageEvent
from app.db.repositories.exceptions import RepositoryError


class UsageAggregateRow(TypedDict):
    resource_key: str
    feature_key: str
    status: str
    event_count: int
    units_total: int


def create_usage_event(session: Session, event: UsageEvent) -> UsageEvent:
    try:
        session.add(event)
        session.flush()
        session.refresh(event)
        return event
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to persist usage event") from exc


def list_account_usage_events(session: Session, *, account_id: int) -> list[UsageEvent]:
    return list_filtered_account_usage_events(session, account_id=account_id)


def list_filtered_account_usage_events(
    session: Session,
    *,
    account_id: int,
    resource_key: str | None = None,
    feature_key: str | None = None,
    status: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort: str = "desc",
    offset: int = 0,
    limit: int = 100,
) -> list[UsageEvent]:
    statement = select(UsageEvent).where(UsageEvent.account_id == account_id)
    if resource_key is not None:
        statement = statement.where(UsageEvent.resource_key == resource_key)
    if feature_key is not None:
        statement = statement.where(UsageEvent.feature_key == feature_key)
    if status is not None:
        statement = statement.where(UsageEvent.status == status)
    if created_after is not None:
        statement = statement.where(UsageEvent.created_at >= created_after)
    if created_before is not None:
        statement = statement.where(UsageEvent.created_at <= created_before)
    if sort == "asc":
        statement = statement.order_by(col(UsageEvent.id).asc())
    else:
        statement = statement.order_by(col(UsageEvent.id).desc())
    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


def count_filtered_account_usage_events(
    session: Session,
    *,
    account_id: int,
    resource_key: str | None = None,
    feature_key: str | None = None,
    status: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> int:
    statement = (
        select(func.count())
        .select_from(UsageEvent)
        .where(UsageEvent.account_id == account_id)
    )
    if resource_key is not None:
        statement = statement.where(UsageEvent.resource_key == resource_key)
    if feature_key is not None:
        statement = statement.where(UsageEvent.feature_key == feature_key)
    if status is not None:
        statement = statement.where(UsageEvent.status == status)
    if created_after is not None:
        statement = statement.where(UsageEvent.created_at >= created_after)
    if created_before is not None:
        statement = statement.where(UsageEvent.created_at <= created_before)
    result = session.exec(statement).one()
    return int(result or 0)


def aggregate_filtered_account_usage_events(
    session: Session,
    *,
    account_id: int,
    resource_key: str | None = None,
    feature_key: str | None = None,
    status: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> list[UsageAggregateRow]:
    resource_key_column = cast(Any, UsageEvent.resource_key)
    feature_key_column = cast(Any, UsageEvent.feature_key)
    status_column = cast(Any, UsageEvent.status)
    units_column = cast(Any, UsageEvent.units)
    statement: Any = (
        select(  # type: ignore[call-overload]
            resource_key_column,
            feature_key_column,
            status_column,
            func.count(),
            func.coalesce(func.sum(units_column), 0),
        )
        .where(UsageEvent.account_id == account_id)
        .group_by(resource_key_column, feature_key_column, status_column)
        .order_by(
            col(resource_key_column).asc(),
            col(feature_key_column).asc(),
            col(status_column).asc(),
        )
    )
    if resource_key is not None:
        statement = statement.where(UsageEvent.resource_key == resource_key)
    if feature_key is not None:
        statement = statement.where(UsageEvent.feature_key == feature_key)
    if status is not None:
        statement = statement.where(UsageEvent.status == status)
    if created_after is not None:
        statement = statement.where(UsageEvent.created_at >= created_after)
    if created_before is not None:
        statement = statement.where(UsageEvent.created_at <= created_before)

    rows = session.exec(statement).all()
    return [
        {
            "resource_key": str(row[0]),
            "feature_key": str(row[1]),
            "status": str(row[2]),
            "event_count": int(row[3] or 0),
            "units_total": int(row[4] or 0),
        }
        for row in rows
    ]
