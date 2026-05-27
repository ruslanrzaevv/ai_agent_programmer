"""
Incident Detector.
Uses a sliding window over Redis log stream to detect error spikes.
Runs as an asyncio task per project.
"""
from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.redis import cache
from app.models.models import LogLevel, Project, User

logger = get_logger("incident_detector")

# Cooldown: don't create another incident for same project within N seconds
INCIDENT_COOLDOWN_SECONDS = 300
# Sliding window for error rate calculation
WINDOW_SECONDS = 60


class ErrorWindow:
    """Sliding window tracking error counts per minute."""

    def __init__(self, window_seconds: int = WINDOW_SECONDS):
        self.window = window_seconds
        self._events: deque[tuple[float, str]] = deque()  # (timestamp, level)

    def add(self, timestamp: float, level: str) -> None:
        self._events.append((timestamp, level))
        self._prune()

    def error_count(self) -> int:
        self._prune()
        return sum(1 for _, l in self._events if l in ("error", "critical"))

    def critical_count(self) -> int:
        self._prune()
        return sum(1 for _, l in self._events if l == "critical")

    def _prune(self) -> None:
        cutoff = asyncio.get_event_loop().time() - self.window
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()


class IncidentDetector:
    """
    Per-project incident detector.
    Subscribes to Redis pub/sub for log events, maintains a sliding window,
    and triggers incident creation when threshold is exceeded.
    """

    def __init__(self, project: Project, db_factory, owner: User):
        self.project = project
        self.db_factory = db_factory  # async context manager factory
        self.owner = owner
        self._window = ErrorWindow()
        self._last_incident_at: float | None = None
        self._pending_logs: list[dict] = []
        self._stop = asyncio.Event()

    async def start(self) -> None:
        logger.info("detector_start", project_id=str(self.project.id))
        asyncio.create_task(self._subscribe_loop())

    async def stop(self) -> None:
        self._stop.set()

    async def handle_log(self, entry: dict) -> None:
        """Called directly from collector callback."""
        level = entry.get("level", "info")
        now = asyncio.get_event_loop().time()
        self._window.add(now, level)

        if level in ("error", "critical"):
            self._pending_logs.append(entry)

        await self._check_threshold()

    async def _subscribe_loop(self) -> None:
        """Subscribe to Redis pub/sub channel for this project's logs."""
        import redis.asyncio as aioredis
        from app.core.config import settings
        import json

        r = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"project:{self.project.id}:logs")

        try:
            async for message in pubsub.listen():
                if self._stop.is_set():
                    break
                if message["type"] != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    if payload.get("type") == "log":
                        await self.handle_log(payload["data"])
                except Exception as e:
                    logger.warning("detector_parse_error", error=str(e))
        finally:
            await pubsub.unsubscribe()
            await r.aclose()

    async def _check_threshold(self) -> None:
        error_count = self._window.error_count()
        threshold = self.project.error_threshold_per_minute

        if error_count < threshold:
            return

        # Cooldown check
        now = asyncio.get_event_loop().time()
        if self._last_incident_at and (now - self._last_incident_at) < INCIDENT_COOLDOWN_SECONDS:
            return

        self._last_incident_at = now
        pending = list(self._pending_logs)
        self._pending_logs.clear()

        logger.info(
            "incident_threshold_crossed",
            project_id=str(self.project.id),
            error_count=error_count,
            threshold=threshold,
        )

        # Create incident in DB
        asyncio.create_task(self._create_incident(pending))

    async def _create_incident(self, log_dicts: list[dict]) -> None:
        from app.services.incident_service import IncidentService
        from app.models.models import LogEntry, LogSource

        try:
            async with self.db_factory() as db:
                # Persist log entries first
                log_objects = []
                for entry in log_dicts[:100]:  # cap at 100 per incident
                    le = LogEntry(
                        project_id=uuid.UUID(entry["project_id"]),
                        source=LogSource(entry["source"]),
                        level=LogLevel(entry["level"]),
                        message=entry["message"],
                        container_name=entry.get("container_name"),
                        service_name=entry.get("service_name"),
                        raw=entry.get("raw", {}),
                        timestamp=datetime.fromisoformat(entry["timestamp"]),
                    )
                    db.add(le)
                    log_objects.append(le)

                await db.flush()

                svc = IncidentService(db)
                await svc.create_from_logs(self.project, log_objects, self.owner)
                await db.commit()

        except Exception as e:
            logger.error("incident_creation_failed", error=str(e), exc_info=True)