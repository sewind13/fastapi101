from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.errors import unwrap_result
from app.api.v1.ops import _to_entitlement_response, _to_usage_event_response
from app.db.models.user import User as UserModel
from app.db.session import get_session
from app.schemas.billing import (
    AccountBillingSummaryResponse,
    AccountEntitlementsResponse,
    AccountUsageReportResponse,
    AccountUsageResponse,
    FeatureBalanceResponse,
    UsageAggregateResponse,
)
from app.services.billing_service import (
    get_account_balance_service,
    get_account_usage_report_service,
    list_account_entitlements_service,
    list_account_usage_service,
)

router = APIRouter()


def _build_usage_response(
    *,
    account_id: int,
    usage_events: list,
    total_count: int,
    offset: int,
    limit: int,
) -> AccountUsageResponse:
    return AccountUsageResponse(
        account_id=account_id,
        total_count=total_count,
        has_next=offset + limit < total_count,
        has_prev=offset > 0,
        usage_events=[_to_usage_event_response(event) for event in usage_events],
    )


def _build_balance_responses(
    *,
    account_id: int,
    entitlements: list,
    session: Session,
) -> list[FeatureBalanceResponse]:
    balances: list[FeatureBalanceResponse] = []
    for resource_key in sorted({item.resource_key for item in entitlements}):
        balance = unwrap_result(
            get_account_balance_service(
                session,
                account_id=account_id,
                resource_key=resource_key,
            )
        )
        balances.append(
            FeatureBalanceResponse(
                account_id=account_id,
                resource_key=resource_key,
                units_remaining=balance,
            )
        )
    return balances


def _build_usage_report_response(
    *,
    account_id: int,
    aggregates: list,
) -> AccountUsageReportResponse:
    return AccountUsageReportResponse(
        account_id=account_id,
        aggregates=[
            UsageAggregateResponse(
                resource_key=str(item["resource_key"]),
                feature_key=str(item["feature_key"]),
                status=str(item["status"]),
                event_count=item["event_count"],
                units_total=item["units_total"],
            )
            for item in aggregates
        ],
    )


@router.get("/me/entitlements", response_model=AccountEntitlementsResponse)
def read_my_entitlements(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    account_id = current_user.account_id
    if account_id is None:
        return AccountEntitlementsResponse(account_id=0, entitlements=[])

    entitlements = unwrap_result(list_account_entitlements_service(session, account_id=account_id))
    return AccountEntitlementsResponse(
        account_id=account_id,
        entitlements=[_to_entitlement_response(item) for item in entitlements],
    )


@router.get("/me/usage", response_model=AccountUsageResponse)
def read_my_usage(
    resource_key: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    account_id = current_user.account_id
    if account_id is None:
        return AccountUsageResponse(
            account_id=0,
            total_count=0,
            has_next=False,
            has_prev=False,
            usage_events=[],
        )

    usage_payload = unwrap_result(
        list_account_usage_service(
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
    )
    usage_events = usage_payload["usage_events"]
    total_count = int(usage_payload["total_count"])
    return _build_usage_response(
        account_id=account_id,
        total_count=total_count,
        usage_events=usage_events,
        offset=offset,
        limit=limit,
    )


@router.get("/me/summary", response_model=AccountBillingSummaryResponse)
def read_my_billing_summary(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    account_id = current_user.account_id
    if account_id is None:
        return AccountBillingSummaryResponse(
            account_id=0,
            entitlements=[],
            balances=[],
            recent_usage_events=[],
        )

    entitlements = unwrap_result(list_account_entitlements_service(session, account_id=account_id))
    usage_payload = unwrap_result(list_account_usage_service(session, account_id=account_id))
    usage_events = usage_payload["usage_events"]
    return AccountBillingSummaryResponse(
        account_id=account_id,
        entitlements=[_to_entitlement_response(item) for item in entitlements],
        balances=_build_balance_responses(
            account_id=account_id,
            entitlements=entitlements,
            session=session,
        ),
        recent_usage_events=[_to_usage_event_response(event) for event in usage_events[:10]],
    )


@router.get("/me/usage/report", response_model=AccountUsageReportResponse)
def read_my_usage_report(
    resource_key: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    account_id = current_user.account_id
    if account_id is None:
        return AccountUsageReportResponse(account_id=0, aggregates=[])

    aggregates = unwrap_result(
        get_account_usage_report_service(
            session,
            account_id=account_id,
            resource_key=resource_key,
            feature_key=feature_key,
            status=status,
            created_after=created_after,
            created_before=created_before,
        )
    )
    return _build_usage_report_response(account_id=account_id, aggregates=aggregates)


@router.get("/me/balance/{resource_key}", response_model=FeatureBalanceResponse)
def read_my_balance(
    resource_key: str,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_current_user),
):
    account_id = current_user.account_id
    if account_id is None:
        return FeatureBalanceResponse(account_id=0, resource_key=resource_key, units_remaining=0)

    balance = unwrap_result(
        get_account_balance_service(
            session,
            account_id=account_id,
            resource_key=resource_key,
        )
    )
    return FeatureBalanceResponse(
        account_id=account_id,
        resource_key=resource_key,
        units_remaining=balance,
    )
