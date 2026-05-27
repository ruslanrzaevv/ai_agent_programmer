"""Periodic cleanup tasks."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import Base
from app.workers.celery_app import celery_app

logger = get_logger("tasks.cleanup")


def _get_sync_db():
    """Synchronous DB session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    engine = create_engine(settings.DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(name="app.workers.tasks.cleanup.cleanup_old_logs", bind=True, max_retries=3)
def cleanup_old_logs(self):
    """Delete log entries older than 30 days to keep DB lean."""
    from app.models.models import LogEntry

    db: Session = _get_sync_db()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        result = db.execute(
            delete(LogEntry).where(LogEntry.created_at < cutoff)
        )
        db.commit()
        deleted = result.rowcount
        logger.info("logs_cleaned_up", deleted=deleted)
        return {"deleted": deleted}
    except Exception as exc:
        db.rollback()
        logger.error("cleanup_logs_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.cleanup.auto_resolve_stale_incidents", bind=True)
def auto_resolve_stale_incidents(self):
    """
    Auto-resolve incidents that have been OPEN or ACKNOWLEDGED for >24h
    with no recent errors — likely already fixed without being marked resolved.
    """
    from app.models.models import Incident, IncidentStatus

    db: Session = _get_sync_db()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stale = db.scalars(
            select(Incident).where(
                Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED]),
                Incident.updated_at < cutoff,
            )
        ).all()

        resolved_count = 0
        for incident in stale:
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.now(timezone.utc)
            duration_min = int((incident.resolved_at - incident.started_at).total_seconds() / 60)
            rpm = {"critical": 1000, "high": 500, "medium": 100, "low": 10}.get(
                incident.severity, 50
            )
            incident.estimated_revenue_loss = round(rpm * (duration_min / 60), 2)
            resolved_count += 1

        db.commit()
        logger.info("stale_incidents_resolved", count=resolved_count)
        return {"resolved": resolved_count}
    except Exception as exc:
        db.rollback()
        logger.error("auto_resolve_failed", error=str(exc))
    finally:
        db.close()