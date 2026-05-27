"""
Container metrics collection.
Runs every 60s via Celery Beat.
Collects CPU + memory stats from all monitored Docker containers
and appends them to active incident timelines (Incident Replay enrichment)
and publishes to Redis for realtime WebSocket push.
"""
import json
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger("tasks.metrics")


@celery_app.task(name="app.workers.tasks.metrics.collect_all_metrics", bind=True)
def collect_all_metrics(self):
    """Collect Docker stats for all active projects."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.models import Incident, IncidentStatus, Project

    engine = create_engine(settings.DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    import redis as sync_redis
    r = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)

    try:
        projects = db.scalars(
            select(Project).where(Project.is_active == True, Project.monitoring_enabled == True)  # noqa: E712
        ).all()

        for project in projects:
            try:
                stats = _collect_docker_stats(project)
                if not stats:
                    continue

                # Publish to realtime WebSocket subscribers
                r.publish(
                    f"project:{project.id}:metrics",
                    json.dumps({
                        "type": "metric",
                        "project_id": str(project.id),
                        "data": stats,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }),
                )

                # Enrich open incident timelines
                open_incidents = db.scalars(
                    select(Incident).where(
                        Incident.project_id == project.id,
                        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED]),
                    )
                ).all()

                for incident in open_incidents:
                    _append_metric_to_timeline(incident, stats)

                db.commit()

            except Exception as e:
                logger.warning("metrics_project_failed", project_id=str(project.id), error=str(e))

    finally:
        db.close()
        r.close()


def _collect_docker_stats(project) -> dict | None:
    """Collect aggregate CPU/memory across all containers for a project."""
    try:
        import docker
        from app.workers.docker_collector import _build_docker_client

        client = _build_docker_client(project)
        filters = {"status": "running"}
        name_filter = project.docker_container_filter.get("name")
        if name_filter:
            filters["name"] = name_filter

        containers = client.containers.list(filters=filters)
        if not containers:
            return None

        total_cpu = 0.0
        total_mem_mb = 0.0
        container_stats = []

        for container in containers:
            try:
                raw = container.stats(stream=False)
                cpu_pct = _calc_cpu_percent(raw)
                mem_usage = raw["memory_stats"].get("usage", 0) / (1024 * 1024)  # → MB
                total_cpu += cpu_pct
                total_mem_mb += mem_usage
                container_stats.append({
                    "name": container.name,
                    "cpu_percent": round(cpu_pct, 2),
                    "memory_mb": round(mem_usage, 2),
                })
            except Exception:
                pass

        return {
            "cpu_percent": round(total_cpu / len(containers), 2),
            "memory_mb": round(total_mem_mb, 2),
            "container_count": len(containers),
            "containers": container_stats,
        }
    except Exception as e:
        logger.warning("docker_stats_failed", error=str(e))
        return None


def _calc_cpu_percent(stats: dict) -> float:
    """Calculate CPU usage % from Docker stats snapshot."""
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"].get("online_cpus") or len(
            stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])
        )
        if system_delta > 0:
            return (cpu_delta / system_delta) * num_cpus * 100.0
    except (KeyError, ZeroDivisionError):
        pass
    return 0.0


def _append_metric_to_timeline(incident, stats: dict) -> None:
    """Find the latest timeline point and enrich it with metrics."""
    timeline = list(incident.timeline or [])
    if not timeline:
        return

    # Update the last point's CPU/memory if not already set
    last = timeline[-1]
    if last.get("cpu_percent") is None:
        last["cpu_percent"] = stats.get("cpu_percent")
        last["memory_mb"] = stats.get("memory_mb")
        timeline[-1] = last
        incident.timeline = timeline