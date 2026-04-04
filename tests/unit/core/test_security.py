import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    get_password_hash,
    validate_password_policy,
    verify_password,
)


def test_password_hash_roundtrip():
    password = "supersecret123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_create_access_token_contains_subject():
    token = create_access_token(subject="123", username="alice")
    payload = jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
        issuer=settings.security.issuer,
        audience=settings.security.audience,
    )

    assert payload["sub"] == "123"
    assert payload["username"] == "alice"
    assert payload["token_type"] == "access"
    assert "exp" in payload


def test_create_email_verification_token_uses_expected_token_type():
    token = create_email_verification_token(subject="123", username="alice")
    payload = jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
        issuer=settings.security.issuer,
        audience=settings.security.audience,
    )

    assert payload["sub"] == "123"
    assert payload["username"] == "alice"
    assert payload["token_type"] == "email_verification"


def test_create_password_reset_token_uses_expected_token_type():
    token = create_password_reset_token(subject="123", username="alice")
    payload = jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
        issuer=settings.security.issuer,
        audience=settings.security.audience,
    )

    assert payload["sub"] == "123"
    assert payload["username"] == "alice"
    assert payload["token_type"] == "password_reset"


def test_validate_password_policy_rejects_username_in_password():
    message = validate_password_policy(
        "alice-password",
        username="alice",
        email="alice@example.com",
    )

    assert message == "Password must not contain the username."
