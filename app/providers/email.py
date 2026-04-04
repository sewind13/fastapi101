import smtplib
from email.message import EmailMessage
from json import dumps
from typing import Protocol
from urllib import request

from app.core.config import settings
from app.core.logging import logger
from app.core.resilience import get_event_retry_policy, is_retryable_http_error, retry_call


class EmailProvider(Protocol):
    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None: ...

    def send_password_reset_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        reset_url: object,
    ) -> None: ...

    def send_verification_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        verification_url: object,
    ) -> None: ...


class ConsoleEmailProvider:
    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None:
        self._log_skip(
            task_name="email.send_welcome",
            user_id=user_id,
            email=email,
            username=username,
        )

    def send_password_reset_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        reset_url: object,
    ) -> None:
        self._log_skip(
            task_name="email.send_password_reset",
            user_id=user_id,
            email=email,
            username=username,
            reset_url=reset_url,
        )

    def send_verification_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        verification_url: object,
    ) -> None:
        self._log_skip(
            task_name="email.send_verification",
            user_id=user_id,
            email=email,
            username=username,
            verification_url=verification_url,
        )

    def _log_skip(self, *, task_name: str, **extra: object) -> None:
        logger.info(
            "skipped email delivery",
            extra={
                "event_type": "email",
                "task_name": task_name,
                **extra,
            },
        )


class SMTPEmailProvider:
    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None:
        self._send_email(
            task_name="email.send_welcome",
            subject="Welcome",
            body=f"Welcome, {username}!",
            email=email,
            extra={"user_id": user_id, "username": username},
        )

    def send_password_reset_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        reset_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_password_reset",
            subject="Reset your password",
            body=f"Hi {username}, reset your password here: {reset_url}",
            email=email,
            extra={"user_id": user_id, "username": username, "reset_url": reset_url},
        )

    def send_verification_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        verification_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_verification",
            subject="Verify your email",
            body=f"Hi {username}, verify your email here: {verification_url}",
            email=email,
            extra={
                "user_id": user_id,
                "username": username,
                "verification_url": verification_url,
            },
        )

    def _send_email(
        self,
        *,
        task_name: str,
        subject: str,
        body: str,
        email: object,
        extra: dict[str, object],
    ) -> None:
        if not settings.email.host:
            raise RuntimeError("EMAIL__HOST is not configured.")
        host = settings.email.host
        policy = get_event_retry_policy(task_name, provider_name="smtp")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email.from_email
        message["To"] = str(email)
        message.set_content(body)

        def send() -> None:
            with smtplib.SMTP(
                host,
                settings.email.port,
                timeout=policy.timeout_seconds,
            ) as smtp:
                if settings.email.use_tls:
                    smtp.starttls()
                if settings.email.username and settings.email.password:
                    smtp.login(settings.email.username, settings.email.password)
                smtp.send_message(message)

        retry_call(
            send,
            is_retryable=lambda exc: isinstance(exc, smtplib.SMTPException | OSError),
            policy=policy,
        )

        logger.info(
            "sent email",
            extra={
                "event_type": "email",
                "task_name": task_name,
                "email": email,
                **extra,
            },
        )


class SendGridEmailProvider:
    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None:
        self._send_email(
            task_name="email.send_welcome",
            email=email,
            subject="Welcome",
            body=f"Welcome, {username}!",
            template_id=settings.email.sendgrid_welcome_template_id,
            template_data={"user_id": user_id, "email": str(email), "username": username},
            extra={"user_id": user_id, "username": username},
        )

    def send_password_reset_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        reset_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_password_reset",
            email=email,
            subject="Reset your password",
            body=f"Hi {username}, reset your password here: {reset_url}",
            template_id=settings.email.sendgrid_password_reset_template_id,
            template_data={
                "user_id": user_id,
                "email": str(email),
                "username": username,
                "reset_url": str(reset_url),
            },
            extra={"user_id": user_id, "username": username, "reset_url": reset_url},
        )

    def send_verification_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        verification_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_verification",
            email=email,
            subject="Verify your email",
            body=f"Hi {username}, verify your email here: {verification_url}",
            template_id=settings.email.sendgrid_verification_template_id,
            template_data={
                "user_id": user_id,
                "email": str(email),
                "username": username,
                "verification_url": str(verification_url),
            },
            extra={
                "user_id": user_id,
                "username": username,
                "verification_url": verification_url,
            },
        )

    def _send_email(
        self,
        *,
        task_name: str,
        email: object,
        subject: str,
        body: str,
        template_id: str | None,
        template_data: dict[str, object],
        extra: dict[str, object],
    ) -> None:
        if not settings.email.sendgrid_api_key:
            raise RuntimeError("EMAIL__SENDGRID_API_KEY is not configured.")
        policy = get_event_retry_policy(task_name, provider_name="sendgrid")

        personalization: dict[str, object] = {"to": [{"email": str(email)}]}
        if settings.email.sendgrid_custom_args:
            personalization["custom_args"] = settings.email.sendgrid_custom_args
        if template_id:
            personalization["dynamic_template_data"] = template_data

        payload_dict: dict[str, object] = {
            "personalizations": [personalization],
            "from": {"email": settings.email.from_email},
        }
        if template_id:
            payload_dict["template_id"] = template_id
        else:
            payload_dict["subject"] = subject
            payload_dict["content"] = [{"type": "text/plain", "value": body}]
        if settings.email.sendgrid_categories:
            payload_dict["categories"] = settings.email.sendgrid_categories

        payload = dumps(payload_dict).encode("utf-8")
        req = request.Request(
            settings.email.sendgrid_api_base_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.email.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        retry_call(
            lambda: request.urlopen(req, timeout=settings.email.sendgrid_timeout_seconds),
            is_retryable=lambda exc: is_retryable_http_error(exc, policy=policy),
            policy=policy,
        ).close()

        logger.info(
            "sent email",
            extra={
                "event_type": "email",
                "provider": "sendgrid",
                "task_name": task_name,
                "email": email,
                **extra,
            },
        )


class SESEmailProvider:
    def send_welcome_email(self, *, user_id: object, email: object, username: object) -> None:
        self._send_email(
            task_name="email.send_welcome",
            email=email,
            subject="Welcome",
            body=f"Welcome, {username}!",
            template_name=settings.email.ses_welcome_template_name,
            template_data={"user_id": user_id, "email": str(email), "username": username},
            extra={"user_id": user_id, "username": username},
        )

    def send_password_reset_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        reset_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_password_reset",
            email=email,
            subject="Reset your password",
            body=f"Hi {username}, reset your password here: {reset_url}",
            template_name=settings.email.ses_password_reset_template_name,
            template_data={
                "user_id": user_id,
                "email": str(email),
                "username": username,
                "reset_url": str(reset_url),
            },
            extra={"user_id": user_id, "username": username, "reset_url": reset_url},
        )

    def send_verification_email(
        self,
        *,
        user_id: object,
        email: object,
        username: object,
        verification_url: object,
    ) -> None:
        self._send_email(
            task_name="email.send_verification",
            email=email,
            subject="Verify your email",
            body=f"Hi {username}, verify your email here: {verification_url}",
            template_name=settings.email.ses_verification_template_name,
            template_data={
                "user_id": user_id,
                "email": str(email),
                "username": username,
                "verification_url": str(verification_url),
            },
            extra={
                "user_id": user_id,
                "username": username,
                "verification_url": verification_url,
            },
        )

    def _send_email(
        self,
        *,
        task_name: str,
        email: object,
        subject: str,
        body: str,
        template_name: str | None,
        template_data: dict[str, object],
        extra: dict[str, object],
    ) -> None:
        import boto3  # type: ignore[import-untyped]
        from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]
        policy = get_event_retry_policy(task_name, provider_name="ses")

        if not settings.email.ses_region:
            raise RuntimeError("EMAIL__SES_REGION is not configured.")

        client_kwargs: dict[str, object] = {"region_name": settings.email.ses_region}
        if settings.email.ses_profile_name:
            session = boto3.Session(profile_name=settings.email.ses_profile_name)
            client = session.client("ses", **client_kwargs)
        else:
            if settings.email.ses_access_key_id and settings.email.ses_secret_access_key:
                client_kwargs["aws_access_key_id"] = settings.email.ses_access_key_id
                client_kwargs["aws_secret_access_key"] = settings.email.ses_secret_access_key
            if settings.email.ses_session_token:
                client_kwargs["aws_session_token"] = settings.email.ses_session_token
            client = boto3.client("ses", **client_kwargs)
        if template_name:
            kwargs = {
                "Source": settings.email.from_email,
                "Destination": {"ToAddresses": [str(email)]},
                "Template": template_name,
                "TemplateData": dumps(template_data),
            }
            if settings.email.ses_configuration_set:
                kwargs["ConfigurationSetName"] = settings.email.ses_configuration_set
            retry_call(
                lambda: client.send_templated_email(**kwargs),
                is_retryable=lambda exc: isinstance(exc, BotoCoreError | ClientError),
                policy=policy,
            )
        else:
            kwargs = {
                "Source": settings.email.from_email,
                "Destination": {"ToAddresses": [str(email)]},
                "Message": {
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}},
                },
            }
            if settings.email.ses_configuration_set:
                kwargs["ConfigurationSetName"] = settings.email.ses_configuration_set
            retry_call(
                lambda: client.send_email(**kwargs),
                is_retryable=lambda exc: isinstance(exc, BotoCoreError | ClientError),
                policy=policy,
            )

        logger.info(
            "sent email",
            extra={
                "event_type": "email",
                "provider": "ses",
                "task_name": task_name,
                "email": email,
                **extra,
            },
        )


def get_email_provider() -> EmailProvider:
    if not settings.email.enabled or settings.email.dry_run:
        return ConsoleEmailProvider()

    if settings.email.provider == "smtp":
        return SMTPEmailProvider()
    if settings.email.provider == "sendgrid":
        return SendGridEmailProvider()
    return SESEmailProvider()
