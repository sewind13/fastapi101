from sqlalchemy import column, desc
from sqlmodel import Session, select

from app.core.cache import cached_json
from app.core.config import settings
from app.db.models.outbox_event import OutboxEvent
from app.db.models.user import User as UserModel
from app.jobs.replay_dead_letter_queue import replay_dead_letter_queue
from app.jobs.report_outbox import report_outbox
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult


class OutboxService(BaseService):
    def get_summary(self, session: Session) -> ServiceResult[dict[str, int]]:
        summary = cached_json(
            "ops:outbox:summary",
            cache_name="outbox_summary",
            loader=lambda: report_outbox(session),
            serializer=lambda value: value,
            deserializer=lambda value: dict(value),
            ttl_seconds=settings.cache.default_ttl_seconds,
        )
        return self.success(summary)

    def list_events(
        self,
        session: Session,
        *,
        status: str | None = None,
        task_name: str | None = None,
        task_id: str | None = None,
        limit: int = 50,
    ) -> ServiceResult[list[OutboxEvent]]:
        statement = select(OutboxEvent).order_by(desc(column("id"))).limit(limit)
        if status:
            statement = statement.where(OutboxEvent.status == status)
        if task_name:
            statement = statement.where(column("task_name").ilike(f"%{task_name}%"))
        if task_id:
            statement = statement.where(column("task_id").ilike(f"%{task_id}%"))
        events = list(session.exec(statement).all())
        return self.success(events)

    def replay_dead_letter(self, *, limit: int = 100) -> ServiceResult[int]:
        replayed = replay_dead_letter_queue(limit=limit)
        return self.success(replayed)

    def get_user_auth_state(self, session: Session, *, user_id: int) -> ServiceResult[UserModel]:
        user = session.get(UserModel, user_id)
        if user is None:
            return self.failure(ErrorCode.USER_NOT_FOUND, "User not found.")
        return self.success(user)

    def unlock_user_account(self, session: Session, *, user_id: int) -> ServiceResult[UserModel]:
        user = session.get(UserModel, user_id)
        if user is None:
            return self.failure(ErrorCode.USER_NOT_FOUND, "User not found.")

        user.failed_login_attempts = 0
        user.locked_until = None
        session.add(user)
        session.commit()
        session.refresh(user)
        return self.success(user)


def get_outbox_summary(session: Session) -> ServiceResult[dict[str, int]]:
    return OutboxService().get_summary(session)


def list_outbox_events(
    session: Session,
    *,
    status: str | None = None,
    task_name: str | None = None,
    task_id: str | None = None,
    limit: int = 50,
) -> ServiceResult[list[OutboxEvent]]:
    return OutboxService().list_events(
        session=session,
        status=status,
        task_name=task_name,
        task_id=task_id,
        limit=limit,
    )


def replay_outbox_dead_letter(*, limit: int = 100) -> ServiceResult[int]:
    return OutboxService().replay_dead_letter(limit=limit)


def get_user_auth_state(session: Session, *, user_id: int) -> ServiceResult[UserModel]:
    return OutboxService().get_user_auth_state(session=session, user_id=user_id)


def unlock_user_account(session: Session, *, user_id: int) -> ServiceResult[UserModel]:
    return OutboxService().unlock_user_account(session=session, user_id=user_id)
