from app.core.logging import configure_logging, logger
from app.core.metrics import observe_maintenance_run
from app.db.session import SessionLocal
from app.services.auth_service import cleanup_revoked_tokens


def main() -> int:
    configure_logging()
    with SessionLocal() as session:
        result = cleanup_revoked_tokens(session=session)

    if not result.ok or result.value is None:
        error = result.error
        observe_maintenance_run(job_name="cleanup_revoked_tokens", outcome="failed")
        logger.error(
            "revoked token cleanup failed",
            extra={
                "event_type": "maintenance",
                "error_code": error.code if error else "unknown_error",
            },
        )
        return 1

    observe_maintenance_run(
        job_name="cleanup_revoked_tokens",
        outcome="succeeded",
        deleted_count=result.value,
    )
    logger.info(
        "revoked token cleanup completed",
        extra={
            "event_type": "maintenance",
            "deleted_count": result.value,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
