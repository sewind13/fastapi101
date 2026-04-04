from app.providers.webhook import get_webhook_provider


def send_user_registered_webhook(*, user_id: object, username: object, email: object) -> None:
    get_webhook_provider().send_user_registered_webhook(
        user_id=user_id,
        username=username,
        email=email,
    )


def send_worker_failure_alert(*, task_name: object, task_id: object, error_message: object) -> None:
    get_webhook_provider().send_worker_failure_alert(
        task_name=task_name,
        task_id=task_id,
        error_message=error_message,
    )
