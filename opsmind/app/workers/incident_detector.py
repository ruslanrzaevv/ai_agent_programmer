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

INCIDENT_COOLDOWN_SECONDS = 300
WINDOW_SECONDS = 60


class ErrorWindow:
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
        import time
        cutoff = time.monotonic() - self.window 
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()


class IncidentDetector:
    def __init__(self, project: Project, db_factory, owner: User):
        self.project = project
        self.db_factory = db_factory  # async context manager factory
        self.owner = owner
        self._window = ErrorWindow()
        self._last_incident_at: float | None = None
        self._pending_logs: list[dict] = []
        self._stop = asyncio.Event()
        from collections import deque
        self._recent_logs = deque(maxlen=500)
        self._last_incident_at: float | None = None
        self._task: asyncio.Task | None = None
        
    async def start(self):
        self._task = asyncio.create_task(
            self._subscribe_loop()
        )

    async def stop(self):
        self._stop.set()

        if self._task:
            self._task.cancel()

            try:
                await self._task
            except asyncio.CancelledError:
                pass


    async def handle_log(self, entry: dict) -> None:
        logger.warning(
            "HANDLE_LOG",
            level=entry.get("level"),
            message=entry.get("message", "")[:100],
        )


        import time
        level = entry.get("level", "info")
        now = time.monotonic()
        self._window.add(now, level)
        self._recent_logs.append(entry)
        if level in ("error", "critical"):
            self._pending_logs.append(entry)
        
        await self._check_threshold()
    


    async def _subscribe_loop(self) -> None:
        import redis.asyncio as aioredis
        from app.core.config import settings
        import json

        while not self._stop.is_set():
            try:
                r = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                pubsub = r.pubsub()
                await pubsub.subscribe(f"project:{self.project.id}:logs")
                logger.info("detector_subscribed", project_id=str(self.project.id))

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
                    try:
                        await r.aclose()
                    except Exception:
                        pass  

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("detector_subscribe_error", error=str(e))
                await asyncio.sleep(5)  

    async def _check_threshold(self) -> None:
        import time

        error_count = self._window.error_count()
        
        logger.warning(
            "CHECK_THRESHOLD",
            errors=self._window.error_count(),
            threshold=self.project.error_threshold_per_minute,
        )
        threshold = self.project.error_threshold_per_minute

        if error_count < threshold:
            return
        
        logger.warning("THRESHOLD_REACHED")

        now = time.monotonic()

        if (
            self._last_incident_at
            and now - self._last_incident_at < INCIDENT_COOLDOWN_SECONDS
        ):
            return

        self._last_incident_at = now

        incident_logs = list(self._recent_logs)
        self._recent_logs.clear()

        await self._create_incident(incident_logs)
        
        
    async def _create_incident(
        self,
        log_dicts: list[dict],
    ) -> None:

        logger.warning("CREATE_INCIDENT_STARTED")

        from app.services.incident_service import IncidentService
        from app.models.models import LogEntry, LogSource

        try:
            async with self.db_factory() as db:

                logger.warning("DB_OPENED")

                log_objects = []

                for entry in log_dicts[:100]:
                    le = LogEntry(
                        project_id=uuid.UUID(entry["project_id"]),
                        source=LogSource(entry["source"]),
                        level=LogLevel(entry["level"]),
                        message=entry["message"],
                        container_name=entry.get("container_name"),
                        service_name=entry.get("service_name"),
                        raw=entry.get("raw", {}),
                        timestamp=datetime.fromisoformat(
                            entry["timestamp"]
                        ),
                    )

                    db.add(le)
                    log_objects.append(le)

                await db.flush()

                logger.warning("BEFORE_CREATE_FROM_LOGS")

                svc = IncidentService(db)

                await svc.create_from_logs(
                    self.project,
                    log_objects,
                    self.owner,
                )

                logger.warning("AFTER_CREATE_FROM_LOGS")

                await db.commit()

        except Exception as e:
            import traceback

            logger.error(
                "INCIDENT_CREATE_FAILED",
                error=str(e),
                traceback=traceback.format_exc(),
            )