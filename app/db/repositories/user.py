from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.db.models.outbox_event import OutboxEvent
from app.db.models.user import User as UserModel
from app.db.repositories.base import BaseRepository
from app.db.repositories.exceptions import RepositoryError


def get_user_by_username(session: Session, username: str) -> UserModel | None:
    statement = select(UserModel).where(UserModel.username == username)
    return session.exec(statement).first()


def get_user_by_email(session: Session, email: str) -> UserModel | None:
    statement = select(UserModel).where(UserModel.email == email)
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: int) -> UserModel | None:
    return session.get(UserModel, user_id)


def user_exists(session: Session, username: str, email: str) -> bool:
    statement = select(UserModel).where(
        (UserModel.username == username) | (UserModel.email == email)
    )
    return session.exec(statement).first() is not None


def create_user(session: Session, user: UserModel) -> UserModel:
    try:
        return BaseRepository[UserModel](session).save(user)
    except RepositoryError as exc:
        raise RepositoryError("Failed to persist user") from exc


def create_user_with_outbox(
    session: Session,
    *,
    user: UserModel,
    outbox_events: list[OutboxEvent],
    after_flush: Callable[[UserModel], list[OutboxEvent]] | None = None,
) -> UserModel:
    try:
        session.add(user)
        session.flush()
        for event in outbox_events:
            if event.payload.get("user_id") is None:
                event.payload["user_id"] = user.id
            session.add(event)
        if after_flush is not None:
            for event in after_flush(user):
                session.add(event)
        session.commit()
        session.refresh(user)
        return user
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to persist user and outbox events") from exc


def register_failed_login(
    session: Session,
    *,
    user: UserModel,
    max_attempts: int,
    lockout_seconds: int,
) -> UserModel:
    try:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = datetime.now(UTC) + timedelta(seconds=lockout_seconds)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to persist failed login state") from exc


def clear_failed_login_state(session: Session, *, user: UserModel) -> UserModel:
    try:
        user.failed_login_attempts = 0
        user.locked_until = None
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to clear failed login state") from exc
