from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "opsmind",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.cleanup",
        "app.workers.tasks.metrics",
        "app.workers.tasks.reports",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Periodic schedule ──────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Clean up old log entries (>30 days) every night at 02:00 UTC
    "cleanup-old-logs": {
        "task": "app.workers.tasks.cleanup.cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),
    },
    # Auto-resolve stale incidents (open for >24h with no new errors) every hour
    "auto-resolve-stale-incidents": {
        "task": "app.workers.tasks.cleanup.auto_resolve_stale_incidents",
        "schedule": crontab(minute=0),
    },
    # Collect Docker container metrics every 60s for Incident Replay enrichment
    "collect-container-metrics": {
        "task": "app.workers.tasks.metrics.collect_all_metrics",
        "schedule": 60.0,
    },
}