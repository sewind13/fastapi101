import argparse
import os

from sqlmodel import Session

from app.core.logging import configure_logging, logger
from app.core.security import get_password_hash, validate_password_policy
from app.db.models.account import Account
from app.db.models.user import User as UserModel
from app.db.repositories.user import get_user_by_email, get_user_by_username
from app.db.session import SessionLocal
from app.schemas.user import USER_ROLES


def _resolve_target_user(
    session: Session,
    *,
    username: str,
    email: str | None,
) -> UserModel | None:
    user_by_username = get_user_by_username(session, username)
    if email is None:
        return user_by_username

    user_by_email = get_user_by_email(session, email)
    if user_by_username and user_by_email and user_by_username.id != user_by_email.id:
        raise ValueError("Provided username and email belong to different users.")
    return user_by_username or user_by_email


def bootstrap_platform_admin(
    *,
    username: str,
    email: str | None = None,
    password: str | None = None,
    role: str = "platform_admin",
    phone: str | None = None,
    verify_email: bool = True,
    activate_user: bool = True,
    session: Session | None = None,
) -> dict[str, str]:
    if role not in USER_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(sorted(USER_ROLES))}.")

    if role == "user":
        raise ValueError("Bootstrap role must be privileged, not 'user'.")

    if session is None:
        with SessionLocal() as managed_session:
            return bootstrap_platform_admin(
                username=username,
                email=email,
                password=password,
                role=role,
                phone=phone,
                verify_email=verify_email,
                activate_user=activate_user,
                session=managed_session,
            )

    user = _resolve_target_user(session, username=username, email=email)

    if user is None:
        if email is None or password is None:
            raise ValueError(
                "email and password are required when bootstrapping a new privileged user."
            )

        password_error = validate_password_policy(password, username=username, email=email)
        if password_error is not None:
            raise ValueError(password_error)

        account = Account(name=f"{username}-account")
        session.add(account)
        session.flush()
        user = UserModel(
            username=username,
            email=email,
            phone=phone,
            hashed_password=get_password_hash(password),
            role=role,
            account_id=account.id,
            is_active=activate_user,
            email_verified=verify_email,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        action = "created"
    else:
        if email is not None and user.email != email:
            raise ValueError("Existing user does not match the provided email.")
        if user.account_id is None:
            account = Account(name=f"{user.username}-account")
            session.add(account)
            session.flush()
            user.account_id = account.id
        user.role = role
        if activate_user:
            user.is_active = True
        if verify_email:
            user.email_verified = True
        session.add(user)
        session.commit()
        session.refresh(user)
        action = "promoted"

    logger.info(
        "bootstrap privileged user completed",
        extra={
            "event_type": "bootstrap",
            "action": action,
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
        },
    )
    return {
        "action": action,
        "username": user.username,
        "role": user.role,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or promote the first privileged user for a new environment."
    )
    parser.add_argument("--username", required=True, help="Username to create or promote.")
    parser.add_argument(
        "--email",
        help=(
            "Email address. Required when creating a new user; "
            "optional when promoting an existing one."
        ),
    )
    parser.add_argument(
        "--password",
        help=(
            "Password. Required when creating a new user; ignored when promoting "
            "an existing one. Prefer --password-env instead of passing a secret on the CLI."
        ),
    )
    parser.add_argument(
        "--password-env",
        default="BOOTSTRAP_ADMIN_PASSWORD",
        help=(
            "Environment variable name that contains the bootstrap password. "
            "Used when --password is omitted."
        ),
    )
    parser.add_argument(
        "--role",
        default="platform_admin",
        choices=sorted(USER_ROLES - {"user"}),
        help="Privileged role to grant.",
    )
    parser.add_argument(
        "--phone",
        default=None,
        help="Optional phone number for new user creation.",
    )
    parser.add_argument(
        "--no-verify-email",
        action="store_true",
        help="Do not mark the user as email-verified during bootstrap.",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Do not force the user into an active state during bootstrap.",
    )
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    password = args.password
    if password is None and args.password_env:
        password = os.getenv(args.password_env)
    result = bootstrap_platform_admin(
        username=args.username,
        email=args.email,
        password=password,
        role=args.role,
        phone=args.phone,
        verify_email=not args.no_verify_email,
        activate_user=not args.inactive,
    )
    logger.info(
        "bootstrap privileged user summary",
        extra={
            "event_type": "bootstrap",
            **result,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
