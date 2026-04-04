from collections import Counter

from sqlmodel import Session, select

from app.core.logging import configure_logging, logger
from app.db.models.outbox_event import OutboxEvent
from app.db.session import SessionLocal


def report_outbox(session: Session | None = None) -> dict[str, int]:
    if session is None:
        with SessionLocal() as managed_session:
            return report_outbox(managed_session)

    else:
        events = list(session.exec(select(OutboxEvent)).all())

    counts = Counter(event.status for event in events)
    summary = {
        "pending": counts.get("pending", 0),
        "published": counts.get("published", 0),
        "failed": counts.get("failed", 0),
        "total": len(events),
    }
    logger.info(
        "outbox status report",
        extra={
            "event_type": "outbox",
            **summary,
        },
    )
    return summary


def main() -> int:
    configure_logging()
    report_outbox()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
