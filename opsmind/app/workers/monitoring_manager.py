"""
Monitoring Manager.
Manages lifecycle of all per-project collectors and detectors.
Started once when the FastAPI app boots.
"""
from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.models import Project, User
from app.workers.docker_collector import DockerLogCollector
from app.workers.gitlab_collector import GitLabCollector
from app.workers.incident_detector import IncidentDetector

logger = get_logger("monitoring_manager")


@asynccontextmanager
async def get_db_ctx():
    async with AsyncSessionLocal() as db:
        yield db


class MonitoringManager:
    """
    Singleton that tracks all running collectors/detectors.
    Call start_project() when a project is created/enabled,
    stop_project() when disabled/deleted.
    """

    def __init__(self):
        self._docker: dict[str, DockerLogCollector] = {}
        self._gitlab: dict[str, GitLabCollector] = {}
        self._detectors: dict[str, IncidentDetector] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def startup(self) -> None:
        """Load all active projects from DB and start monitoring."""
        logger.info("monitoring_manager_startup")
        async with AsyncSessionLocal() as db:
            projects = await db.scalars(
                select(Project)
                .where(Project.is_active == True, Project.monitoring_enabled == True)  # noqa: E712
                .options(selectinload(Project.owner))
            )
            for project in projects:
                await self.start_project(project, project.owner)
        logger.info("all_projects_started")

    async def shutdown(self) -> None:
        logger.info("monitoring_manager_shutdown")
        for project_id in list(self._docker.keys()):
            await self.stop_project(project_id)

    # ── Per-project management ─────────────────────────────────────────────────

    async def start_project(self, project: Project, owner: User) -> None:
        pid = str(project.id)
        if pid in self._detectors:
            logger.warning("project_already_monitored", project_id=pid)
            return

        logger.info("starting_project_monitoring", project_id=pid, name=project.name)

        detector = IncidentDetector(project, get_db_ctx, owner)
        await detector.start()
        self._detectors[pid] = detector

        async def on_log(entry: dict) -> None:
            await detector.handle_log(entry)

        # Docker collector
        try:
            docker_collector = DockerLogCollector(project, on_log)
            await docker_collector.start()
            self._docker[pid] = docker_collector
        except Exception as e:
            logger.error("docker_collector_start_failed", project_id=pid, error=str(e))

        # GitLab collector
        try:
            gitlab_collector = GitLabCollector(project, on_log)
            await gitlab_collector.start()
            self._gitlab[pid] = gitlab_collector
        except Exception as e:
            logger.error("gitlab_collector_start_failed", project_id=pid, error=str(e))

        logger.info("project_monitoring_started", project_id=pid)

    async def stop_project(self, project_id: str) -> None:
        logger.info("stopping_project_monitoring", project_id=project_id)

        if collector := self._docker.pop(project_id, None):
            await collector.stop()
        if collector := self._gitlab.pop(project_id, None):
            await collector.stop()
        if detector := self._detectors.pop(project_id, None):
            await detector.stop()

    async def restart_project(self, project_id: str) -> None:
        await self.stop_project(project_id)
        async with AsyncSessionLocal() as db:
            project = await db.scalar(
                select(Project)
                .where(Project.id == uuid.UUID(project_id))
                .options(selectinload(Project.owner))
            )
            if project:
                await self.start_project(project, project.owner)

    def get_gitlab_collector(self, project_id: str) -> GitLabCollector | None:
        return self._gitlab.get(project_id)

    def status(self) -> dict:
        return {
            "monitored_projects": len(self._detectors),
            "docker_collectors": len(self._docker),
            "gitlab_collectors": len(self._gitlab),
            "project_ids": list(self._detectors.keys()),
        }


monitoring_manager = MonitoringManager()