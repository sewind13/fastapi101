from datetime import UTC, datetime, timedelta

from app.db.repositories.revoked_token import delete_expired_tokens, revoke_token


def test_delete_expired_tokens_removes_only_expired_rows(session):
    now = datetime.now(UTC)
    revoke_token(
        session=session,
        jti="expired-token",
        token_type="refresh",
        expires_at=now - timedelta(minutes=5),
    )
    revoke_token(
        session=session,
        jti="active-token",
        token_type="refresh",
        expires_at=now + timedelta(minutes=5),
    )

    deleted_count = delete_expired_tokens(session=session, now=now)

    assert deleted_count == 1


def test_delete_expired_tokens_returns_zero_when_nothing_is_expired(session):
    now = datetime.now(UTC)
    revoke_token(
        session=session,
        jti="still-active-token",
        token_type="refresh",
        expires_at=now + timedelta(minutes=10),
    )

    deleted_count = delete_expired_tokens(session=session, now=now)

    assert deleted_count == 0
