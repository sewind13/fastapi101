import pytest
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.db.base import metadata

sqlite_url = "sqlite://"
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@pytest.fixture
def session():
    metadata.create_all(engine)
    with TestingSessionLocal() as db_session:
        yield db_session
    metadata.drop_all(engine)
