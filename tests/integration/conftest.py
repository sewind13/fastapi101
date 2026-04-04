import os

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from alembic import command
from app.db.base import metadata
from app.db.session import get_session
from app.main import app
from tests.conftest import build_token_headers, create_test_user

sqlite_url = "sqlite://"
sqlite_engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=sqlite_engine,
    class_=Session,
    expire_on_commit=False,
)


@pytest.fixture(name="session")
def session_fixture():
    metadata.create_all(sqlite_engine)
    with TestingSessionLocal() as session:
        yield session
    metadata.drop_all(sqlite_engine)


@pytest.fixture(name="client")
async def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def token_headers(session: Session):
    user = create_test_user(session)
    assert user.id is not None
    return build_token_headers(user.id, user.username)


@pytest.fixture(scope="session")
def postgres_database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set for Postgres integration tests")
    return url


@pytest.fixture(scope="session")
def postgres_engine(postgres_database_url: str):
    engine = create_engine(postgres_database_url, pool_pre_ping=True)

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", postgres_database_url)
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def postgres_session(postgres_engine):
    connection = postgres_engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    nested_transaction = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session_, transaction):
        nonlocal nested_transaction
        if transaction.nested and not nested_transaction.is_active:
            nested_transaction = connection.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", restart_savepoint)
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
async def postgres_client(postgres_session: Session):
    def get_session_override():
        yield postgres_session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def postgres_token_headers(postgres_session: Session):
    user = create_test_user(
        postgres_session,
        username="pg_testuser",
        email="pg_test@example.com",
    )
    assert user.id is not None
    return build_token_headers(user.id, user.username)
