from datetime import UTC, datetime

from sqlmodel import Session, col, select

from app.db.models.usage_reservation import UsageReservation
from app.db.repositories.exceptions import RepositoryError


def create_usage_reservation(
    session: Session,
    reservation: UsageReservation,
) -> UsageReservation:
    try:
        session.add(reservation)
        session.flush()
        session.refresh(reservation)
        return reservation
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to create usage reservation") from exc


def get_reservation_by_id_for_update(
    session: Session,
    *,
    reservation_id: int,
) -> UsageReservation | None:
    statement = (
        select(UsageReservation)
        .where(UsageReservation.id == reservation_id)
        .with_for_update()
    )
    return session.exec(statement).first()


def list_account_reservations(
    session: Session,
    *,
    account_id: int,
) -> list[UsageReservation]:
    statement = (
        select(UsageReservation)
        .where(UsageReservation.account_id == account_id)
        .order_by(col(UsageReservation.id).desc())
    )
    return list(session.exec(statement).all())


def mark_reservation_status(
    session: Session,
    *,
    reservation: UsageReservation,
    status: str,
) -> UsageReservation:
    try:
        reservation.status = status
        reservation.updated_at = datetime.now(UTC)
        session.add(reservation)
        session.flush()
        return reservation
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to update reservation status") from exc
