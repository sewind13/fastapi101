from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import delete
from sqlmodel import Session, select

from app.db.models.revoked_token import RevokedToken
from app.db.repositories.base import BaseRepository
from app.db.repositories.exceptions import RepositoryError


def is_token_revoked(session: Session, jti: str) -> bool:
    statement = select(RevokedToken).where(RevokedToken.jti == jti)
    return session.exec(statement).first() is not None


def revoke_token(
    session: Session,
    *,
    jti: str,
    token_type: str,
    expires_at: datetime,
) -> RevokedToken:
    revoked_token = RevokedToken(
        jti=jti,
        token_type=token_type,
        expires_at=expires_at,
    )
    try:
        return BaseRepository[RevokedToken](session).save(revoked_token)
    except RepositoryError as exc:
        raise RepositoryError("Failed to revoke token") from exc


def delete_expired_tokens(session: Session, *, now: datetime | None = None) -> int:
    cutoff = now or datetime.now(UTC)
    revoked_token_table = cast(Any, RevokedToken).__table__
    statement = delete(RevokedToken).where(revoked_token_table.c.expires_at < cutoff)
    try:
        result = session.exec(statement)
        session.commit()
        return int(result.rowcount or 0)
    except Exception as exc:
        session.rollback()
        raise RepositoryError("Failed to delete expired revoked tokens") from exc
