from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel import Session

from app.db.models.usage_event import UsageEvent
from app.db.models.usage_reservation import UsageReservation
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.feature_entitlement import (
    get_active_entitlement_for_update,
    update_entitlement_usage,
)
from app.db.repositories.usage_event import create_usage_event
from app.db.repositories.usage_reservation import (
    create_usage_reservation,
    get_reservation_by_id_for_update,
    mark_reservation_status,
)
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult

FEATURE_POLICIES: dict[str, dict[str, Any]] = {
    "items.create": {
        "resource_key": "item_create",
        "units_per_call": 1,
        "charge_on": "success",
    },
    "service_a.run": {
        "resource_key": "service_a",
        "units_per_call": 1,
        "charge_on": "success",
    }
}


class EntitlementService(BaseService):
    def reserve_feature_usage(
        self,
        session: Session,
        *,
        account_id: int,
        feature_key: str,
        user_id: int | None,
        request_id: str,
    ) -> ServiceResult[UsageReservation]:
        policy = FEATURE_POLICIES.get(feature_key)
        if policy is None:
            return self.failure(
                ErrorCode.BILLING_FEATURE_NOT_ENABLED,
                f"Feature policy is not configured for {feature_key}.",
            )

        resource_key = str(policy["resource_key"])
        units_per_call = int(policy["units_per_call"])
        entitlement = get_active_entitlement_for_update(
            session,
            account_id=account_id,
            resource_key=resource_key,
        )
        if entitlement is None:
            return self.failure(
                ErrorCode.BILLING_NO_ENTITLEMENT,
                f"No active entitlement found for {resource_key}.",
            )

        if entitlement.valid_until is not None and entitlement.valid_until < datetime.now(UTC):
            return self.failure(
                ErrorCode.BILLING_ENTITLEMENT_EXPIRED,
                f"Entitlement for {resource_key} has expired.",
            )

        remaining_units = entitlement.units_total - entitlement.units_used
        if remaining_units < units_per_call:
            return self.failure(
                ErrorCode.BILLING_QUOTA_EXHAUSTED,
                f"Quota exhausted for {resource_key}.",
            )

        reservation = UsageReservation(
            account_id=account_id,
            entitlement_id=entitlement.id or 0,
            user_id=user_id,
            resource_key=resource_key,
            feature_key=feature_key,
            units_reserved=units_per_call,
            request_id=request_id,
            status="active",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        try:
            created = create_usage_reservation(session, reservation)
            session.commit()
            return self.success(created)
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to reserve usage right now.",
            )

    def commit_reserved_usage(
        self,
        session: Session,
        *,
        reservation_id: int,
    ) -> ServiceResult[UsageEvent]:
        reservation = get_reservation_by_id_for_update(session, reservation_id=reservation_id)
        if reservation is None:
            return self.failure(
                ErrorCode.BILLING_RESERVATION_NOT_FOUND,
                "Usage reservation not found.",
            )
        if reservation.status != "active":
            return self.failure(
                ErrorCode.BILLING_INVALID_RESERVATION_STATE,
                "Usage reservation is not active.",
            )

        entitlement = get_active_entitlement_for_update(
            session,
            account_id=reservation.account_id,
            resource_key=reservation.resource_key,
        )
        if entitlement is None or entitlement.id != reservation.entitlement_id:
            return self.failure(
                ErrorCode.BILLING_NO_ENTITLEMENT,
                "Active entitlement was not found for this reservation.",
            )

        try:
            update_entitlement_usage(
                session,
                entitlement=entitlement,
                units_delta=reservation.units_reserved,
            )
            mark_reservation_status(session, reservation=reservation, status="committed")
            usage_event = create_usage_event(
                session,
                UsageEvent(
                    account_id=reservation.account_id,
                    entitlement_id=reservation.entitlement_id,
                    reservation_id=reservation.id,
                    user_id=reservation.user_id,
                    resource_key=reservation.resource_key,
                    feature_key=reservation.feature_key,
                    units=reservation.units_reserved,
                    request_id=reservation.request_id,
                    status="committed",
                ),
            )
            session.commit()
            return self.success(usage_event)
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to commit reserved usage right now.",
            )

    def release_reserved_usage(
        self,
        session: Session,
        *,
        reservation_id: int,
    ) -> ServiceResult[None]:
        reservation = get_reservation_by_id_for_update(session, reservation_id=reservation_id)
        if reservation is None:
            return self.failure(
                ErrorCode.BILLING_RESERVATION_NOT_FOUND,
                "Usage reservation not found.",
            )
        if reservation.status != "active":
            return self.failure(
                ErrorCode.BILLING_INVALID_RESERVATION_STATE,
                "Usage reservation is not active.",
            )

        try:
            mark_reservation_status(session, reservation=reservation, status="released")
            session.commit()
            return self.success(None)
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to release reserved usage right now.",
            )

    def run_with_reserved_usage[T](
        self,
        session: Session,
        *,
        account_id: int,
        feature_key: str,
        user_id: int | None,
        request_id: str,
        operation: Callable[[], T],
    ) -> ServiceResult[T]:
        reservation_result = self.reserve_feature_usage(
            session,
            account_id=account_id,
            feature_key=feature_key,
            user_id=user_id,
            request_id=request_id,
        )
        if not reservation_result.ok or reservation_result.value is None:
            return ServiceResult(error=reservation_result.error)

        reservation = reservation_result.value
        try:
            value = operation()
        except Exception:
            self.release_reserved_usage(session, reservation_id=reservation.id or 0)
            raise

        commit_result = self.commit_reserved_usage(session, reservation_id=reservation.id or 0)
        if not commit_result.ok:
            return ServiceResult(error=commit_result.error)
        return self.success(value)


def reserve_feature_usage(
    session: Session,
    *,
    account_id: int,
    feature_key: str,
    user_id: int | None,
    request_id: str,
) -> ServiceResult[UsageReservation]:
    return EntitlementService().reserve_feature_usage(
        session,
        account_id=account_id,
        feature_key=feature_key,
        user_id=user_id,
        request_id=request_id,
    )


def commit_reserved_usage(
    session: Session,
    *,
    reservation_id: int,
) -> ServiceResult[UsageEvent]:
    return EntitlementService().commit_reserved_usage(session, reservation_id=reservation_id)


def release_reserved_usage(
    session: Session,
    *,
    reservation_id: int,
) -> ServiceResult[None]:
    return EntitlementService().release_reserved_usage(session, reservation_id=reservation_id)
