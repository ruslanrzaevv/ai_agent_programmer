"""
GitLab event collector.
Handles incoming webhook events AND polls GitLab API for pipeline status.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
from datetime import datetime, timezone

import gitlab
import gitlab.exceptions
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.logging import get_logger
from app.db.redis import cache
from app.models.models import LogLevel, LogSource, Project

logger = get_logger("gitlab_collector")


class GitLabCollector:
    """
    Per-project GitLab collector.
    - Polls pipeline/job status every 60s
    - Processes inbound webhook events (see webhook endpoint)
    - Publishes log entries to Redis just like Docker collector
    """

    def __init__(self, project: Project, on_log_callback):
        self.project = project
        self.on_log = on_log_callback
        self._stop = asyncio.Event()
        self._gl: gitlab.Gitlab | None = None
        self._gl_project = None

    async def start(self) -> None:
        logger.info("gitlab_collector_start", project_id=str(self.project.id))
        asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._stop.set()

    # ── Polling loop ──────────────────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self._poll_pipelines()
            except Exception as e:
                logger.error("gitlab_poll_error", error=str(e))
            await asyncio.sleep(60)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=False)
    async def _poll_pipelines(self) -> None:
        loop = asyncio.get_event_loop()
        gl = await loop.run_in_executor(None, self._get_gl_client)
        gl_project = await loop.run_in_executor(
            None, lambda: gl.projects.get(self.project.gitlab_project_id)
        )
        pipelines = await loop.run_in_executor(
            None, lambda: gl_project.pipelines.list(per_page=5, order_by="updated_at")
        )

        for pipeline in pipelines:
            if pipeline.status in ("failed", "canceled"):
                await self._emit_pipeline_event(pipeline, gl_project)

    async def _emit_pipeline_event(self, pipeline, gl_project) -> None:
        loop = asyncio.get_event_loop()
        jobs = await loop.run_in_executor(None, lambda: pipeline.jobs.list())
        failed_jobs = [j for j in jobs if j.status == "failed"]

        for job in failed_jobs:
            log_text = ""
            try:
                log_text = await loop.run_in_executor(None, lambda: gl_project.jobs.get(job.id).trace())
                if isinstance(log_text, bytes):
                    log_text = log_text.decode("utf-8", errors="replace")
                log_text = log_text[-3000:]  # last 3000 chars
            except Exception:
                pass

            message = (
                f"GitLab pipeline #{pipeline.id} FAILED — "
                f"job '{job.name}' on branch '{pipeline.ref}'. "
                f"Triggered by: {pipeline.user.get('name', 'unknown') if pipeline.user else 'scheduler'}"
            )
            if log_text:
                message += f"\n\nJob log tail:\n{log_text}"

            entry = {
                "project_id": str(self.project.id),
                "source": LogSource.GITLAB.value,
                "level": LogLevel.ERROR.value,
                "message": message[:8192],
                "container_name": None,
                "service_name": f"gitlab-pipeline-{pipeline.id}",
                "raw": {
                    "pipeline_id": pipeline.id,
                    "job_id": job.id,
                    "job_name": job.name,
                    "branch": pipeline.ref,
                    "status": pipeline.status,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await cache.lpush(f"logs:{self.project.id}", entry)
            await cache.publish(f"project:{self.project.id}:logs", {"type": "log", "data": entry})
            await self.on_log(entry)
            logger.info("gitlab_pipeline_logged", pipeline_id=pipeline.id, job=job.name)

    # ── Webhook processor ─────────────────────────────────────────────────────

    async def process_webhook(self, payload: dict, token: str | None = None) -> None:
        """Called from the webhook HTTP endpoint."""
        if self.project.gitlab_webhook_secret and token != self.project.gitlab_webhook_secret:
            raise ValueError("Invalid webhook token")

        event_type = payload.get("object_kind")

        if event_type == "pipeline":
            await self._handle_pipeline_webhook(payload)
        elif event_type == "build":
            await self._handle_job_webhook(payload)
        elif event_type == "push":
            await self._handle_push_webhook(payload)

    async def _handle_pipeline_webhook(self, payload: dict) -> None:
        attrs = payload.get("object_attributes", {})
        status = attrs.get("status")
        if status not in ("failed", "canceled"):
            return

        entry = {
            "project_id": str(self.project.id),
            "source": LogSource.GITLAB.value,
            "level": LogLevel.ERROR.value,
            "message": (
                f"Pipeline #{attrs.get('id')} {status.upper()} "
                f"on '{attrs.get('ref')}' — {attrs.get('sha', '')[:8]}"
            ),
            "service_name": "gitlab-webhook",
            "raw": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await cache.lpush(f"logs:{self.project.id}", entry)
        await cache.publish(f"project:{self.project.id}:logs", {"type": "log", "data": entry})
        await self.on_log(entry)

    async def _handle_job_webhook(self, payload: dict) -> None:
        if payload.get("build_status") not in ("failed",):
            return
        entry = {
            "project_id": str(self.project.id),
            "source": LogSource.GITLAB.value,
            "level": LogLevel.ERROR.value,
            "message": (
                f"Job '{payload.get('build_name')}' FAILED in pipeline #{payload.get('pipeline_id')} "
                f"on '{payload.get('ref')}'"
            ),
            "service_name": "gitlab-job",
            "raw": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await cache.lpush(f"logs:{self.project.id}", entry)
        await self.on_log(entry)

    async def _handle_push_webhook(self, payload: dict) -> None:
        """Log every push to main/master as an informational event (for Incident Replay context)."""
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        if branch not in self.project.gitlab_branches:
            return
        commits = payload.get("commits", [])
        entry = {
            "project_id": str(self.project.id),
            "source": LogSource.GITLAB.value,
            "level": LogLevel.INFO.value,
            "message": (
                f"Push to '{branch}': {len(commits)} commit(s) by "
                f"{payload.get('user_name', 'unknown')}"
            ),
            "service_name": "gitlab-push",
            "raw": {"branch": branch, "commit_count": len(commits)},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await cache.lpush(f"logs:{self.project.id}", entry)
        await cache.publish(f"project:{self.project.id}:logs", {"type": "log", "data": entry})

    def _get_gl_client(self) -> gitlab.Gitlab:
        if self._gl is None:
            self._gl = gitlab.Gitlab(
                self.project.gitlab_url,
                private_token=self.project.gitlab_token,
                ssl_verify=True,
            )
        return self._gl