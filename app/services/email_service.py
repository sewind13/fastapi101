from app.providers.email import get_email_provider


def send_welcome_email(*, user_id: object, email: object, username: object) -> None:
    get_email_provider().send_welcome_email(
        user_id=user_id,
        email=email,
        username=username,
    )


def send_password_reset_email(
    *,
    user_id: object,
    email: object,
    username: object,
    reset_url: object,
) -> None:
    get_email_provider().send_password_reset_email(
        user_id=user_id,
        email=email,
        username=username,
        reset_url=reset_url,
    )


def send_verification_email(
    *,
    user_id: object,
    email: object,
    username: object,
    verification_url: object,
) -> None:
    get_email_provider().send_verification_email(
        user_id=user_id,
        email=email,
        username=username,
        verification_url=verification_url,
    )
