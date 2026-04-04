from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session

from app.api.deps import get_operations_user
from app.api.errors import unwrap_result
from app.core.logging import log_audit_event
from app.core.request import get_request_id
from app.db.models.user import User as UserModel
from app.db.session import get_session
from app.schemas.billing import (
    AccountEntitlementsResponse,
    AccountUsageReportResponse,
    AccountUsageResponse,
    FeatureEntitlementResponse,
    GrantEntitlementRequest,
    UsageAggregateResponse,
    UsageEventResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.ops import (
    AccountEntitlementBalanceResponse,
    DeadLetterReplayResponse,
    OutboxEventResponse,
    OutboxSummaryResponse,
    UserAuthStateResponse,
)
from app.services.billing_service import (
    get_account_balance_service,
    get_account_usage_report_service,
    grant_entitlement,
    list_account_entitlements_service,
    list_account_usage_service,
)
from app.services.outbox_service import (
    get_outbox_summary,
    get_user_auth_state,
    list_outbox_events,
    replay_outbox_dead_letter,
    unlock_user_account,
)

router = APIRouter()


def _to_entitlement_response(entitlement) -> FeatureEntitlementResponse:
    return FeatureEntitlementResponse(
        id=entitlement.id or 0,
        account_id=entitlement.account_id,
        resource_key=entitlement.resource_key,
        units_total=entitlement.units_total,
        units_used=entitlement.units_used,
        units_remaining=entitlement.units_total - entitlement.units_used,
        status=entitlement.status,
        valid_from=entitlement.valid_from,
        valid_until=entitlement.valid_until,
        source_type=entitlement.source_type,
        source_id=entitlement.source_id,
    )


def _to_usage_event_response(event) -> UsageEventResponse:
    return UsageEventResponse(
        id=event.id or 0,
        account_id=event.account_id,
        entitlement_id=event.entitlement_id,
        reservation_id=event.reservation_id,
        resource_key=event.resource_key,
        feature_key=event.feature_key,
        units=event.units,
        user_id=event.user_id,
        request_id=event.request_id,
        status=event.status,
        created_at=event.created_at,
    )


def _build_ops_usage_response(
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


def _build_ops_usage_report_response(
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


@router.get("/outbox/summary", response_model=OutboxSummaryResponse)
def read_outbox_summary(
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    return unwrap_result(get_outbox_summary(session))


@router.get("/outbox/events", response_model=list[OutboxEventResponse])
def read_outbox_events(
    status: str | None = Query(default=None),
    task_name: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    return unwrap_result(
        list_outbox_events(
            session=session,
            status=status,
            task_name=task_name,
            task_id=task_id,
            limit=limit,
        )
    )


@router.post("/outbox/replay-dlq", response_model=DeadLetterReplayResponse)
def replay_dead_letter(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    replayed = unwrap_result(replay_outbox_dead_letter(limit=limit))
    return DeadLetterReplayResponse(replayed=replayed)


@router.get(
    "/billing/accounts/{account_id}/entitlements",
    response_model=AccountEntitlementsResponse,
)
def read_account_entitlements(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    entitlements = unwrap_result(list_account_entitlements_service(session, account_id=account_id))
    return AccountEntitlementsResponse(
        account_id=account_id,
        entitlements=[_to_entitlement_response(item) for item in entitlements],
    )


@router.get(
    "/billing/accounts/{account_id}/usage",
    response_model=AccountUsageResponse,
)
def read_account_usage(
    account_id: int,
    resource_key: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
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
    return _build_ops_usage_response(
        account_id=account_id,
        total_count=total_count,
        usage_events=usage_events,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/billing/accounts/{account_id}/usage/report",
    response_model=AccountUsageReportResponse,
)
def read_account_usage_report(
    account_id: int,
    resource_key: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
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
    return _build_ops_usage_report_response(account_id=account_id, aggregates=aggregates)


@router.get(
    "/billing/accounts/{account_id}/balance/{resource_key}",
    response_model=AccountEntitlementBalanceResponse,
)
def read_account_balance(
    account_id: int,
    resource_key: str,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    balance = unwrap_result(
        get_account_balance_service(
            session,
            account_id=account_id,
            resource_key=resource_key,
        )
    )
    return AccountEntitlementBalanceResponse(
        account_id=account_id,
        resource_key=resource_key,
        units_remaining=balance,
    )


@router.post(
    "/billing/accounts/{account_id}/grant",
    response_model=FeatureEntitlementResponse,
)
def create_account_entitlement(
    account_id: int,
    entitlement_in: GrantEntitlementRequest,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    del current_user
    entitlement = unwrap_result(
        grant_entitlement(
            session,
            account_id=account_id,
            resource_key=entitlement_in.resource_key,
            units_total=entitlement_in.units_total,
            source_type=entitlement_in.source_type,
            source_id=entitlement_in.source_id,
            valid_until=entitlement_in.valid_until,
        )
    )
    return _to_entitlement_response(entitlement)


@router.get("/users/{user_id}/auth-state", response_model=UserAuthStateResponse)
def read_user_auth_state(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    user = unwrap_result(get_user_auth_state(session=session, user_id=user_id))
    locked_until = user.locked_until
    if locked_until is not None and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    return UserAuthStateResponse(
        id=user.id or user_id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=locked_until,
        is_locked=bool(locked_until and locked_until > datetime.now(UTC)),
    )


@router.post("/users/{user_id}/unlock", response_model=MessageResponse)
def unlock_user_auth_state(
    user_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: UserModel = Depends(get_operations_user),
):
    unlocked_user = unwrap_result(unlock_user_account(session=session, user_id=user_id))
    log_audit_event(
        "ops.user.unlock.succeeded",
        event_type="ops",
        actor_username=current_user.username,
        target_user_id=unlocked_user.id,
        request_id=get_request_id(request),
    )
    return MessageResponse(message="User account lockout cleared.")
