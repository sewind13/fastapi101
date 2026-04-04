from datetime import UTC, datetime

from sqlmodel import Session

from app.core.config import settings
from app.core.security import (
    build_email_verification_url,
    create_email_verification_token,
    get_password_hash,
    validate_password_policy,
)
from app.db.models.account import Account
from app.db.models.outbox_event import OutboxEvent
from app.db.models.user import User as UserModel
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.user import create_user_with_outbox as repo_create_user_with_outbox
from app.db.repositories.user import get_user_by_id as repo_get_user_by_id
from app.db.repositories.user import user_exists
from app.schemas.user import UserCreate
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult
from app.worker.outbox import (
    build_user_registered_outbox_event,
    build_user_registered_webhook_outbox_event,
    build_verification_email_outbox_event,
    build_welcome_email_outbox_event,
)
from app.worker.schemas import (
    UserRegisteredPayload,
    VerificationEmailPayload,
    WelcomeEmailPayload,
)


class UserService(BaseService):
    def create_user(
        self,
        session: Session,
        user_in: UserCreate,
        *,
        request_id: str | None = None,
    ) -> ServiceResult[UserModel]:
        password_error = validate_password_policy(
            user_in.password,
            username=user_in.username,
            email=user_in.email,
        )
        if password_error is not None:
            return self.failure(ErrorCode.SECURITY_WEAK_PASSWORD, password_error)

        if user_exists(session=session, username=user_in.username, email=user_in.email):
            return self.failure(
                ErrorCode.USER_CONFLICT,
                "A user with this username or email already exists.",
            )

        user_data = user_in.model_dump(exclude={"password"})
        account = Account(name=f"{user_in.username}-account")
        session.add(account)
        session.flush()
        db_user = UserModel(
            **user_data,
            hashed_password=get_password_hash(user_in.password),
            email_verified=not settings.security.email_verification_enabled,
            account_id=account.id,
        )
        user_registered_payload = UserRegisteredPayload(
            user_id=None,
            username=user_in.username,
            email=user_in.email,
        )
        welcome_email_payload = WelcomeEmailPayload(
            user_id=None,
            username=user_in.username,
            email=user_in.email,
        )
        outbox_events: list[OutboxEvent] = [
            build_user_registered_outbox_event(
                payload=user_registered_payload,
                request_id=request_id,
                source="api.users.register",
            ),
            build_welcome_email_outbox_event(
                payload=welcome_email_payload,
                request_id=request_id,
                source="api.users.register",
            ),
            build_user_registered_webhook_outbox_event(
                payload=user_registered_payload,
                request_id=request_id,
                source="api.users.register",
            ),
        ]

        def after_flush(user: UserModel) -> list[OutboxEvent]:
            if not settings.security.email_verification_enabled or user.id is None:
                return []

            verification_token = create_email_verification_token(
                subject=str(user.id),
                username=user.username,
            )
            verification_url = build_email_verification_url(token=verification_token)
            user.email_verification_sent_at = datetime.now(UTC)
            return [
                build_verification_email_outbox_event(
                    payload=VerificationEmailPayload(
                        user_id=user.id,
                        username=user.username,
                        email=user.email,
                        verification_url=verification_url,
                    ),
                    request_id=request_id,
                    source="api.users.register",
                )
            ]

        try:
            return self.success(
                repo_create_user_with_outbox(
                    session=session,
                    user=db_user,
                    outbox_events=outbox_events,
                    after_flush=after_flush,
                )
            )
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to create the user right now.",
            )

    def get_user_by_id(self, session: Session, user_id: int) -> ServiceResult[UserModel]:
        user = repo_get_user_by_id(session=session, user_id=user_id)
        if not user:
            return self.failure(ErrorCode.USER_NOT_FOUND, f"User {user_id} was not found.")

        return self.success(user)


def create_user(
    session: Session,
    user_in: UserCreate,
    *,
    request_id: str | None = None,
) -> ServiceResult[UserModel]:
    service = UserService()
    return service.create_user(session=session, user_in=user_in, request_id=request_id)


def get_user_by_id(session: Session, user_id: int) -> ServiceResult[UserModel]:
    service = UserService()
    return service.get_user_by_id(session=session, user_id=user_id)
