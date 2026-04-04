from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.repositories.revoked_token import revoke_token
from app.services.auth_service import authenticate_user, cleanup_revoked_tokens
from app.services.exceptions import ErrorCode


def test_cleanup_revoked_tokens_returns_deleted_count(session):
    now = datetime.now(UTC)
    revoke_token(
        session=session,
        jti="cleanup-expired-token",
        token_type="refresh",
        expires_at=now - timedelta(minutes=1),
    )
    revoke_token(
        session=session,
        jti="cleanup-active-token",
        token_type="refresh",
        expires_at=now + timedelta(minutes=10),
    )

    result = cleanup_revoked_tokens(session=session)

    assert result.ok is True
    assert result.value == 1


def test_authenticate_user_locks_account_after_failed_attempt_threshold(session, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_enabled", True)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_max_attempts", 2)
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_seconds", 300)

    user = User(
        username="locked-user",
        email="locked@example.com",
        hashed_password=get_password_hash("correct-password"),
    )
    session.add(user)
    session.commit()

    first_attempt = authenticate_user(session, "locked-user", "wrong-password")
    second_attempt = authenticate_user(session, "locked-user", "wrong-password")

    session.refresh(user)

    assert first_attempt.ok is False
    assert first_attempt.error is not None
    assert first_attempt.error.code == ErrorCode.AUTH_INVALID_CREDENTIALS
    assert second_attempt.ok is False
    assert second_attempt.error is not None
    assert second_attempt.error.code == ErrorCode.AUTH_ACCOUNT_LOCKED
    assert user.failed_login_attempts == 2
    assert user.locked_until is not None


def test_authenticate_user_success_clears_failed_login_state(session, monkeypatch):
    monkeypatch.setattr(settings.auth_rate_limit, "account_lockout_enabled", True)

    user = User(
        username="reset-user",
        email="reset@example.com",
        hashed_password=get_password_hash("correct-password"),
        failed_login_attempts=3,
        locked_until=datetime.now(UTC) - timedelta(minutes=1),
    )
    session.add(user)
    session.commit()

    result = authenticate_user(session, "reset-user", "correct-password")

    session.refresh(user)

    assert result.ok is True
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
