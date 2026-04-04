from typing import TypeVar

from sqlmodel import Session

from app.db.repositories.exceptions import RepositoryError

ModelT = TypeVar("ModelT")


class BaseRepository[ModelT]:
    def __init__(self, session: Session):
        self.session = session

    def save(self, instance: ModelT) -> ModelT:
        try:
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except Exception as exc:
            self.session.rollback()
            raise RepositoryError("Failed to persist entity") from exc
