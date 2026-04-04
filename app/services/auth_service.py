from datetime import UTC, datetime

from sqlmodel import Session

from app.core.config import settings
from app.core.security import (
    build_email_verification_url,
    build_password_reset_url,
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    decode_token_payload,
    get_password_hash,
    validate_password_policy,
    verify_password,
)
from app.db.models.outbox_event import OutboxEvent
from app.db.models.user import User as UserModel
from app.db.repositories.exceptions import RepositoryError
from app.db.repositories.outbox_event import create_outbox_events
from app.db.repositories.revoked_token import (
    delete_expired_tokens,
    is_token_revoked,
    revoke_token,
)
from app.db.repositories.user import (
    clear_failed_login_state,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    register_failed_login,
)
from app.schemas.token import TokenPair
from app.services.exceptions import ErrorCode
from app.services.result import BaseService, ServiceResult
from app.worker.outbox import (
    build_password_reset_email_outbox_event,
    build_verification_email_outbox_event,
)
from app.worker.schemas import PasswordResetEmailPayload, VerificationEmailPayload


class AuthService(BaseService):
    def _normalize_utc(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def authenticate_user(
        self, session: Session, username: str, password: str
    ) -> ServiceResult[TokenPair]:
        user = get_user_by_username(session=session, username=username)
        now = datetime.now(UTC)
        locked_until = self._normalize_utc(user.locked_until) if user else None

        if user and locked_until and locked_until > now:
            return self.failure(
                ErrorCode.AUTH_ACCOUNT_LOCKED,
                "This account is temporarily locked. Please try again later.",
            )

        if not user or not verify_password(password, user.hashed_password):
            if user and settings.auth_rate_limit.account_lockout_enabled:
                try:
                    user = register_failed_login(
                        session=session,
                        user=user,
                        max_attempts=settings.auth_rate_limit.account_lockout_max_attempts,
                        lockout_seconds=settings.auth_rate_limit.account_lockout_seconds,
                    )
                except RepositoryError:
                    return self.failure(
                        ErrorCode.COMMON_INTERNAL_ERROR,
                        "Unable to verify your credentials right now.",
                    )

                locked_until = self._normalize_utc(user.locked_until)
                if locked_until and locked_until > now:
                    return self.failure(
                        ErrorCode.AUTH_ACCOUNT_LOCKED,
                        "This account is temporarily locked. Please try again later.",
                    )

            return self.failure(
                ErrorCode.AUTH_INVALID_CREDENTIALS,
                "Invalid username or password.",
            )

        if not user.is_active:
            return self.failure(ErrorCode.AUTH_INACTIVE_USER, "This account is inactive.")

        if settings.security.require_verified_email_for_login and not user.email_verified:
            return self.failure(
                ErrorCode.AUTH_EMAIL_NOT_VERIFIED,
                "This account must verify its email address before signing in.",
            )

        if user.failed_login_attempts > 0 or user.locked_until is not None:
            try:
                clear_failed_login_state(session=session, user=user)
            except RepositoryError:
                return self.failure(
                    ErrorCode.COMMON_INTERNAL_ERROR,
                    "Unable to complete sign-in right now.",
                )

        return self.success(
            TokenPair(
                access_token=create_access_token(
                    subject=str(user.id),
                    username=user.username,
                ),
                refresh_token=create_refresh_token(
                    subject=str(user.id),
                    username=user.username,
                ),
                access_expires_in=settings.security.access_token_expire_minutes * 60,
                refresh_expires_in=settings.security.refresh_token_expire_minutes * 60,
            )
        )

    def refresh_tokens(self, session: Session, refresh_token: str) -> ServiceResult[TokenPair]:
        try:
            token_data = decode_token(refresh_token)
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        if token_data.token_type != "refresh":
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        if is_token_revoked(session=session, jti=token_data.jti):
            return self.failure(
                ErrorCode.AUTH_REFRESH_REUSED,
                "Refresh token has already been revoked.",
            )

        user = get_user_by_id(session=session, user_id=int(token_data.sub))
        if not user or not user.is_active:
            return self.failure(ErrorCode.AUTH_INVALID_TOKEN, "Unable to authenticate this token.")

        try:
            payload = decode_token_payload(refresh_token)
            expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
            revoke_token(
                session=session,
                jti=token_data.jti,
                token_type=token_data.token_type,
                expires_at=expires_at,
            )
        except RepositoryError:
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to rotate the refresh token right now.",
            )
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        return self.success(
            TokenPair(
                access_token=create_access_token(
                    subject=str(user.id),
                    username=user.username,
                ),
                refresh_token=create_refresh_token(
                    subject=str(user.id),
                    username=user.username,
                ),
                access_expires_in=settings.security.access_token_expire_minutes * 60,
                refresh_expires_in=settings.security.refresh_token_expire_minutes * 60,
            )
        )

    def logout_refresh_token(self, session: Session, refresh_token: str) -> ServiceResult[str]:
        try:
            token_data = decode_token(refresh_token)
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        if token_data.token_type != "refresh":
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        if is_token_revoked(session=session, jti=token_data.jti):
            return self.failure(
                ErrorCode.AUTH_REFRESH_REUSED,
                "Refresh token has already been revoked.",
            )

        try:
            payload = decode_token_payload(refresh_token)
            expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
            revoke_token(
                session=session,
                jti=token_data.jti,
                token_type=token_data.token_type,
                expires_at=expires_at,
            )
        except RepositoryError:
            return self.failure(ErrorCode.COMMON_INTERNAL_ERROR, "Unable to log out right now.")
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Refresh token is invalid or expired.",
            )

        return self.success("Logged out successfully")

    def request_email_verification(
        self,
        session: Session,
        *,
        user: UserModel,
    ) -> ServiceResult[str]:
        if user.email_verified:
            return self.success("Email is already verified.")

        token = create_email_verification_token(subject=str(user.id), username=user.username)
        verification_url = build_email_verification_url(token=token)
        event: OutboxEvent = build_verification_email_outbox_event(
            payload=VerificationEmailPayload(
                user_id=user.id,
                username=user.username,
                email=user.email,
                verification_url=verification_url,
            ),
            request_id=None,
            source="api.auth.verify_email",
        )

        try:
            create_outbox_events(session, [event])
            user.email_verification_sent_at = datetime.now(UTC)
            session.add(user)
            session.commit()
            session.refresh(user)
        except RepositoryError:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to queue the verification email right now.",
            )
        except Exception:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to queue the verification email right now.",
            )

        return self.success("Verification email queued.")

    def request_password_reset(self, session: Session, *, email: str) -> ServiceResult[str]:
        user = get_user_by_email(session=session, email=email)
        if user is None:
            return self.success(
                "If an account exists for that email address, "
                "a password reset email has been queued."
            )

        token = create_password_reset_token(subject=str(user.id), username=user.username)
        reset_url = build_password_reset_url(token=token)
        event: OutboxEvent = build_password_reset_email_outbox_event(
            payload=PasswordResetEmailPayload(
                user_id=user.id,
                username=user.username,
                email=user.email,
                reset_url=reset_url,
            ),
            request_id=None,
            source="api.auth.password_reset",
        )

        try:
            create_outbox_events(session, [event])
            session.commit()
        except RepositoryError:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to queue the password reset email right now.",
            )
        except Exception:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to queue the password reset email right now.",
            )

        return self.success(
            "If an account exists for that email address, "
            "a password reset email has been queued."
        )

    def confirm_password_reset(
        self,
        session: Session,
        *,
        token: str,
        new_password: str,
    ) -> ServiceResult[str]:
        try:
            token_data = decode_token(token)
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Password reset token is invalid or expired.",
            )

        if token_data.token_type != "password_reset":
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Password reset token is invalid or expired.",
            )

        user = get_user_by_id(session=session, user_id=int(token_data.sub))
        if not user or user.username != token_data.username:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Password reset token is invalid or expired.",
            )

        password_error = validate_password_policy(
            new_password,
            username=user.username,
            email=user.email,
        )
        if password_error is not None:
            return self.failure(ErrorCode.SECURITY_WEAK_PASSWORD, password_error)

        try:
            user.hashed_password = get_password_hash(new_password)
            user.failed_login_attempts = 0
            user.locked_until = None
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to reset the password right now.",
            )

        return self.success("Password reset successfully.")

    def confirm_email_verification(self, session: Session, *, token: str) -> ServiceResult[str]:
        try:
            token_data = decode_token(token)
        except Exception:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Verification token is invalid or expired.",
            )

        if token_data.token_type != "email_verification":
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Verification token is invalid or expired.",
            )

        user = get_user_by_id(session=session, user_id=int(token_data.sub))
        if not user or user.username != token_data.username:
            return self.failure(
                ErrorCode.AUTH_INVALID_TOKEN,
                "Verification token is invalid or expired.",
            )

        if user.email_verified:
            return self.success("Email is already verified.")

        try:
            user.email_verified = True
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception:
            session.rollback()
            return self.failure(
                ErrorCode.COMMON_INTERNAL_ERROR,
                "Unable to verify the email right now.",
            )

        return self.success("Email verified successfully.")


def authenticate_user(session: Session, username: str, password: str) -> ServiceResult[TokenPair]:
    service = AuthService()
    return service.authenticate_user(session=session, username=username, password=password)


def refresh_tokens(session: Session, refresh_token: str) -> ServiceResult[TokenPair]:
    service = AuthService()
    return service.refresh_tokens(session=session, refresh_token=refresh_token)


def logout_refresh_token(session: Session, refresh_token: str) -> ServiceResult[str]:
    service = AuthService()
    return service.logout_refresh_token(session=session, refresh_token=refresh_token)


def request_email_verification(
    session: Session,
    *,
    user: UserModel,
) -> ServiceResult[str]:
    service = AuthService()
    return service.request_email_verification(session=session, user=user)


def confirm_email_verification(session: Session, *, token: str) -> ServiceResult[str]:
    service = AuthService()
    return service.confirm_email_verification(session=session, token=token)


def request_password_reset(session: Session, *, email: str) -> ServiceResult[str]:
    service = AuthService()
    return service.request_password_reset(session=session, email=email)


def confirm_password_reset(
    session: Session,
    *,
    token: str,
    new_password: str,
) -> ServiceResult[str]:
    service = AuthService()
    return service.confirm_password_reset(
        session=session,
        token=token,
        new_password=new_password,
    )


def cleanup_revoked_tokens(session: Session) -> ServiceResult[int]:
    service = AuthService()
    try:
        deleted_count = delete_expired_tokens(session=session)
    except RepositoryError:
        return service.failure(
            ErrorCode.COMMON_INTERNAL_ERROR,
            "Unable to clean up expired revoked tokens right now.",
        )
    return service.success(deleted_count)
