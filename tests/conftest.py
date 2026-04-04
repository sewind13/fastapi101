import os

import pytest

os.environ.setdefault("APP__ENV", "testing")
os.environ.setdefault("API__PUBLIC_REGISTRATION_ENABLED", "true")
os.environ.setdefault("METRICS__ENABLED", "true")
os.environ.setdefault("METRICS__AUTH_TOKEN", "")
os.environ.setdefault(
    "SECURITY__SECRET_KEY",
    "test-secret-key-32-characters-minimum!!",
)
os.environ.setdefault("SECURITY__REQUIRE_VERIFIED_EMAIL_FOR_LOGIN", "false")

from app.core.rate_limit import login_rate_limiter, token_rate_limiter
from app.core.security import create_access_token, get_password_hash
from app.db.models.account import Account
from app.db.models.user import User


def create_test_user(
    session,
    *,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
    role: str = "user",
) -> User:
    account = Account(name=f"{username}-account")
    session.add(account)
    session.flush()
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        account_id=account.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def build_token_headers(user_id: int, username: str) -> dict[str, str]:
    token = create_access_token(subject=str(user_id), username=username)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    login_rate_limiter.clear()
    token_rate_limiter.clear()
    yield
    login_rate_limiter.clear()
    token_rate_limiter.clear()
