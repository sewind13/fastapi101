from datetime import UTC, datetime

from sqlmodel import Session

from app.db.models.feature_entitlement import FeatureEntitlement
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.feature_entitlement import (
    create_feature_entitlement,
    list_account_entitlements,
    sum_remaining_units,
)
from app.db.repositories.usage_event import (
    UsageAggregateRow,
    aggregate_filtered_account_usage_events,
    count_filtered_account_usage_events,
    list_filtered_account_usage_events,
)
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult


class BillingService(BaseService):
    def grant_entitlement(
        self,
        session: Session,
        *,
        account_id: int,
        resource_key: str,
        units_total: int,
        source_type: str = "grant",
        source_id: str | None = None,
        valid_until: datetime | None = None,
    ) -> ServiceResult[FeatureEntitlement]:
        if units_total <= 0:
            return self.failure(
                ErrorCode.BILLING_INVALID_ENTITLEMENT,
                "Entitlement units_total must be greater than zero.",
            )

        entitlement = FeatureEntitlement(
            account_id=account_id,
            resource_key=resource_key,
            units_total=units_total,
            units_used=0,
            status="active",
            valid_from=datetime.now(UTC),
            valid_until=valid_until,
            source_type=source_type,
            source_id=source_id,
        )
        try:
            created = create_feature_entitlement(session, entitlement)
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to grant entitlement right now.",
            )
        return self.success(created)

    def list_entitlements(
        self,
        session: Session,
        *,
        account_id: int,
    ) -> ServiceResult[list[FeatureEntitlement]]:
        return self.success(list_account_entitlements(session, account_id=account_id))

    def list_usage(
        self,
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
    ) -> ServiceResult[dict[str, object]]:
        usage_events = list_filtered_account_usage_events(
            session,
            account_id=account_id,
            resource_key=resource_key,
            feature_key=feature_key,
            status=status,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            offset=offset,
            limit=limit,
        )
        total_count = count_filtered_account_usage_events(
            session,
            account_id=account_id,
            resource_key=resource_key,
            feature_key=feature_key,
            status=status,
            created_after=created_after,
            created_before=created_before,
        )
        return self.success(
            {
                "usage_events": usage_events,
                "total_count": total_count,
            }
        )

    def get_balance(
        self,
        session: Session,
        *,
        account_id: int,
        resource_key: str,
    ) -> ServiceResult[int]:
        return self.success(
            sum_remaining_units(session, account_id=account_id, resource_key=resource_key)
        )

    def usage_report(
        self,
        session: Session,
        *,
        account_id: int,
        resource_key: str | None = None,
        feature_key: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> ServiceResult[list[UsageAggregateRow]]:
        return self.success(
            aggregate_filtered_account_usage_events(
                session,
                account_id=account_id,
                resource_key=resource_key,
                feature_key=feature_key,
                status=status,
                created_after=created_after,
                created_before=created_before,
            )
        )


def grant_entitlement(
    session: Session,
    *,
    account_id: int,
    resource_key: str,
    units_total: int,
    source_type: str = "grant",
    source_id: str | None = None,
    valid_until: datetime | None = None,
) -> ServiceResult[FeatureEntitlement]:
    return BillingService().grant_entitlement(
        session,
        account_id=account_id,
        resource_key=resource_key,
        units_total=units_total,
        source_type=source_type,
        source_id=source_id,
        valid_until=valid_until,
    )


def list_account_entitlements_service(
    session: Session,
    *,
    account_id: int,
) -> ServiceResult[list[FeatureEntitlement]]:
    return BillingService().list_entitlements(session, account_id=account_id)


def list_account_usage_service(
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
) -> ServiceResult[dict[str, object]]:
    return BillingService().list_usage(
        session,
        account_id=account_id,
        resource_key=resource_key,
        feature_key=feature_key,
        status=status,
        created_after=created_after,
        created_before=created_before,
        sort=sort,
        offset=offset,
        limit=limit,
    )


def get_account_balance_service(
    session: Session,
    *,
    account_id: int,
    resource_key: str,
) -> ServiceResult[int]:
    return BillingService().get_balance(
        session,
        account_id=account_id,
        resource_key=resource_key,
    )


def get_account_usage_report_service(
    session: Session,
    *,
    account_id: int,
    resource_key: str | None = None,
    feature_key: str | None = None,
    status: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> ServiceResult[list[UsageAggregateRow]]:
    return BillingService().usage_report(
        session,
        account_id=account_id,
        resource_key=resource_key,
        feature_key=feature_key,
        status=status,
        created_after=created_after,
        created_before=created_before,
    )
