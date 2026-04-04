from sqlmodel import Session, select

from app.db.models.account import Account
from app.db.repositories.base import BaseRepository
from app.db.repositories.exceptions import RepositoryError


def get_account_by_id(session: Session, account_id: int) -> Account | None:
    return session.get(Account, account_id)


def get_account_by_name(session: Session, name: str) -> Account | None:
    statement = select(Account).where(Account.name == name)
    return session.exec(statement).first()


def create_account(session: Session, account: Account) -> Account:
    try:
        return BaseRepository[Account](session).save(account)
    except RepositoryError as exc:
        raise RepositoryError("Failed to persist account") from exc
