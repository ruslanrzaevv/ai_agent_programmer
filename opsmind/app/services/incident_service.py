"""Incident lifecycle service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.redis import cache
from app.models.models import (
    Incident, IncidentLog, IncidentSeverity,
    IncidentStatus, LogEntry, LogLevel, Project, User,
)
from app.services.ai_service import AIService
from app.services.notification_service import NotificationService

logger = get_logger("incidents")


def _classify_severity(error_count: int, critical_count: int) -> IncidentSeverity:
    if critical_count > 0 or error_count >= 50:
        return IncidentSeverity.CRITICAL
    if error_count >= 20:
        return IncidentSeverity.HIGH
    if error_count >= 5:
        return IncidentSeverity.MEDIUM
    return IncidentSeverity.LOW


class IncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService()

    # ── Create incident from detected log spike ────────────────────────────────

    async def create_from_logs(
        self,
        project: Project,
        triggering_logs: list[LogEntry],
        owner: User,
    ) -> Incident:
        critical_count = sum(1 for l in triggering_logs if l.level == LogLevel.CRITICAL)
        severity = _classify_severity(len(triggering_logs), critical_count)

        first_log = triggering_logs[0]
        title = self._generate_title(triggering_logs)
        containers = list({l.container_name for l in triggering_logs if l.container_name})

        incident = Incident(
            project_id=project.id,
            title=title,
            severity=severity,
            status=IncidentStatus.OPEN,
            error_count=len(triggering_logs),
            affected_containers=containers,
            started_at=first_log.timestamp,
            timeline=[],
        )
        self.db.add(incident)
        await self.db.flush()

        # Link logs
        for log in triggering_logs:
            self.db.add(IncidentLog(incident_id=incident.id, log_entry_id=log.id))

        await self.db.flush()
        logger.info("incident_created", incident_id=str(incident.id), severity=severity)

        # AI analysis (async, may take a few seconds)
        try:
            explanations = await self.ai.explain_all_modes(incident, triggering_logs)
            incident.ai_explanation_junior = explanations.get("junior")
            incident.ai_explanation_senior = explanations.get("senior")
            incident.ai_explanation_ceo = explanations.get("ceo")

            fix = await self.ai.suggest_fix(incident, triggering_logs)
            incident.ai_fix_suggestion = fix["description"]
            incident.ai_auto_fix_script = fix["script"] or None
        except Exception as e:
            logger.error("ai_analysis_failed", error=str(e))

        # Build initial timeline
        incident.timeline = self._build_timeline(triggering_logs)

        # Publish to WebSocket subscribers
        await cache.publish(
            f"project:{project.id}:incidents",
            {
                "type": "incident_created",
                "incident_id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
            },
        )

        # Send notifications
        notif_svc = NotificationService(self.db)
        await notif_svc.notify_incident(incident, project, [owner])

        return incident

    # ── Acknowledge ────────────────────────────────────────────────────────────

    async def acknowledge(self, incident_id: uuid.UUID, user_id: uuid.UUID) -> Incident:
        incident = await self._get_or_raise(incident_id)
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = datetime.now(timezone.utc)
        incident.acknowledged_by_id = user_id
        await self.db.flush()
        return incident

    # ── Resolve ────────────────────────────────────────────────────────────────

    async def resolve(self, incident_id: uuid.UUID) -> Incident:
        incident = await self._get_or_raise(incident_id)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(timezone.utc)

        duration_min = int((incident.resolved_at - incident.started_at).total_seconds() / 60)
        # Rough revenue loss estimate: $1000/hr for critical
        rpm = {"critical": 1000, "high": 500, "medium": 100, "low": 10}.get(incident.severity, 50)
        incident.estimated_revenue_loss = round(rpm * (duration_min / 60), 2)

        await self.db.flush()
        logger.info("incident_resolved", incident_id=str(incident_id), duration_min=duration_min)
        return incident

    # ── Apply AI fix ───────────────────────────────────────────────────────────

    async def apply_fix(self, incident_id: uuid.UUID, confirmed: bool) -> dict:
        incident = await self._get_or_raise(incident_id)
        if not incident.ai_auto_fix_script:
            return {"success": False, "message": "No auto-fix script available"}
        if not confirmed:
            return {
                "success": False,
                "message": "Confirmation required",
                "script_preview": incident.ai_auto_fix_script,
            }

        # NOTE: In production, this would execute via a sandboxed job runner
        # with full audit logging. For safety, we just mark it as applied here.
        incident.ai_fix_applied = True
        incident.ai_fix_applied_at = datetime.now(timezone.utc)
        incident.status = IncidentStatus.RESOLVING
        await self.db.flush()
        return {"success": True, "message": "Fix marked as applied. Execute the script on your server."}

    # ── Append timeline point (called from realtime worker) ───────────────────

    async def append_timeline_point(
        self,
        incident_id: uuid.UUID,
        point: dict,
    ) -> None:
        incident = await self._get_or_raise(incident_id)
        timeline = list(incident.timeline or [])
        timeline.append(point)
        incident.timeline = timeline
        await self.db.flush()

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _get_or_raise(self, incident_id: uuid.UUID) -> Incident:
        incident = await self.db.scalar(
            select(Incident)
            .where(Incident.id == incident_id)
            .options(selectinload(Incident.logs))
        )
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        return incident

    @staticmethod
    def _generate_title(logs: list[LogEntry]) -> str:
        """Generate a descriptive title from the most common error."""
        error_msgs = [l.message for l in logs if l.level in (LogLevel.ERROR, LogLevel.CRITICAL)]
        if error_msgs:
            # Take the most common prefix
            first = error_msgs[0][:120]
            return f"{len(logs)} errors — {first}" if len(first) < 100 else first
        return f"Incident: {len(logs)} anomalies detected"

    @staticmethod
    def _build_timeline(logs: list[LogEntry]) -> list[dict]:
        """Build minute-by-minute timeline from logs."""
        if not logs:
            return []

        start = logs[0].timestamp
        by_minute: dict[int, list[LogEntry]] = {}

        for log in logs:
            minute = int((log.timestamp - start).total_seconds() / 60)
            by_minute.setdefault(minute, []).append(log)

        timeline = []
        for minute in sorted(by_minute.keys()):
            bucket = by_minute[minute]
            errors = [l for l in bucket if l.level in (LogLevel.ERROR, LogLevel.CRITICAL)]
            containers = list({l.container_name for l in bucket if l.container_name})
            first_event = bucket[0].message[:200] if bucket else ""

            from datetime import timedelta
            ts = start + timedelta(minutes=minute)

            timeline.append({
                "minute": minute,
                "ts": ts.isoformat(),
                "event": first_event,
                "error_count": len(errors),
                "request_count": len(bucket),
                "containers": containers,
                "cpu_percent": None,    # filled by metrics worker
                "memory_mb": None,
                "first_failing_endpoint": None,
            })

        return timeline