from datetime import UTC, datetime, timedelta
from urllib.parse import quote
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import settings
from app.schemas.token import TokenData


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def _create_token(
    *,
    subject: str,
    username: str,
    token_type: str,
    expires_minutes: int,
) -> str:
    issued_at = datetime.now(UTC)
    expire = issued_at + timedelta(minutes=expires_minutes)
    to_encode = {
        "sub": subject,
        "username": username,
        "token_type": token_type,
        "iss": settings.security.issuer,
        "aud": settings.security.audience,
        "jti": str(uuid4()),
        "iat": issued_at,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )
    return encoded_jwt


def create_access_token(*, subject: str, username: str) -> str:
    return _create_token(
        subject=subject,
        username=username,
        token_type="access",
        expires_minutes=settings.security.access_token_expire_minutes,
    )


def create_refresh_token(*, subject: str, username: str) -> str:
    return _create_token(
        subject=subject,
        username=username,
        token_type="refresh",
        expires_minutes=settings.security.refresh_token_expire_minutes,
    )


def create_email_verification_token(*, subject: str, username: str) -> str:
    return _create_token(
        subject=subject,
        username=username,
        token_type="email_verification",
        expires_minutes=settings.security.email_verification_token_expire_minutes,
    )


def create_password_reset_token(*, subject: str, username: str) -> str:
    return _create_token(
        subject=subject,
        username=username,
        token_type="password_reset",
        expires_minutes=settings.security.email_verification_token_expire_minutes,
    )


def build_email_verification_url(*, token: str) -> str:
    base_url = settings.app.public_base_url.rstrip("/")
    return f"{base_url}{settings.api.v1_prefix}/auth/verify-email/confirm?token={quote(token)}"


def build_password_reset_url(*, token: str) -> str:
    base_url = settings.app.public_base_url.rstrip("/")
    return f"{base_url}{settings.api.v1_prefix}/auth/password-reset/confirm?token={quote(token)}"


def validate_password_policy(
    password: str,
    *,
    username: str | None = None,
    email: str | None = None,
) -> str | None:
    if len(password) < settings.security.password_min_length:
        return (
            f"Password must be at least {settings.security.password_min_length} characters long."
        )
    if settings.security.password_require_uppercase and not any(
        char.isupper() for char in password
    ):
        return "Password must include at least one uppercase letter."
    if settings.security.password_require_lowercase and not any(
        char.islower() for char in password
    ):
        return "Password must include at least one lowercase letter."
    if settings.security.password_require_digit and not any(char.isdigit() for char in password):
        return "Password must include at least one digit."
    if settings.security.password_require_special and not any(
        not char.isalnum() for char in password
    ):
        return "Password must include at least one special character."
    if settings.security.password_forbid_username and username:
        if username.lower() in password.lower():
            return "Password must not contain the username."
    if settings.security.password_forbid_email_localpart and email:
        local_part = email.split("@", 1)[0].lower()
        if local_part and local_part in password.lower():
            return "Password must not contain the email local part."
    return None


def decode_token(token: str) -> TokenData:
    payload = decode_token_payload(token)
    return TokenData.model_validate(payload)


def decode_token_payload(token: str) -> dict:
    return jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
        issuer=settings.security.issuer,
        audience=settings.security.audience,
    )
