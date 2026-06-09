from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
import gitlab
import ast
import re

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
from app.services.gitlab_service import GitLabService

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


    async def create_from_logs(
        self,
        project: Project,
        triggering_logs: list[LogEntry],
        owner: User,
    ) -> Incident:
        triggering_logs = sorted(
            triggering_logs,
            key=lambda x: x.timestamp,
        )
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

        for log in triggering_logs:
            self.db.add(IncidentLog(incident_id=incident.id, log_entry_id=log.id))

        await self.db.flush()
        logger.info("incident_created", incident_id=str(incident.id), severity=severity)

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

        incident.timeline = self._build_timeline(triggering_logs)

        from app.db.redis import get_redis
        import json
        r = await get_redis()
        await r.publish(
            f"project:{project.id}:incidents",
            json.dumps({
                "type": "incident_created",
                "incident_id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
            }, default=str)
        )


        notif_svc = NotificationService(self.db)
        await notif_svc.notify_incident(incident, project, [owner])

        return incident


    async def acknowledge(self, incident_id: uuid.UUID, user_id: uuid.UUID) -> Incident:
        incident = await self._get_or_raise(incident_id)
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = datetime.now(timezone.utc)
        incident.acknowledged_by_id = user_id
        await self.db.flush()
        return incident


    async def resolve(self, incident_id: uuid.UUID) -> Incident:
        incident = await self._get_or_raise(incident_id)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(timezone.utc)

        duration_min = int((incident.resolved_at - incident.started_at).total_seconds() / 60)
        rpm = {"critical": 1000, "high": 500, "medium": 100, "low": 10}.get(incident.severity, 50)
        incident.estimated_revenue_loss = round(rpm * (duration_min / 60), 2)

        await self.db.flush()
        logger.info("incident_resolved", incident_id=str(incident_id), duration_min=duration_min)
        return incident


    async def apply_fix(self,incident_id: uuid.UUID,confirmed: bool,):
        incident = await self._get_or_raise(
            incident_id
        )

        if not confirmed:
            return {
                "success": False,
                "message": "Confirmation required",
            }

        if not incident.ai_fix_file:
            return {
                "success": False,
                "message": "Generate fix first",
            }

        project = await self.db.get(
            Project,
            incident.project_id,
        )

        gitlab = GitLabService(
            project.gitlab_url,
            project.gitlab_token,
            project.gitlab_project_id,
        )

        branch_name = (
            f"opsmind-fix-{incident.id}"
        )

        try:

            
            review = await self.ai.review_patch(
                incident.ai_fix_old_code,
                incident.ai_fix_new_code,
            )
            
            try:
                ast.parse(
                    incident.ai_fix_new_code
                )
            except SyntaxError as e:

                return {
                    "success": False,
                    "message": f"Syntax error: {e}",
                }

            review_data = json.loads(review)

            if not review_data["safe"]:
                return {
                    "success": False,
                    "message": review_data["reason"],
                }
            gitlab.create_branch(branch_name)

            gitlab.update_file(
                branch=branch_name,
                file_path=incident.ai_fix_file,
                content=incident.ai_fix_new_code,
                commit_message="OpsMind AI Auto Fix",
            )

            mr = gitlab.create_merge_request(
                source_branch=branch_name,
                target_branch="main", 
            )

            incident.ai_fix_applied = True

            incident.ai_fix_applied_at = (
                datetime.now(timezone.utc)
            )

            incident.ai_merge_request_url = (
                mr.web_url
            )

            incident.status = (
                IncidentStatus.RESOLVING
            )

            await self.db.flush()

            return {
                "success": True,
                "merge_request_url": mr.web_url,
                "branch": branch_name,
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e),
            }


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
        error_msgs = [
            l.message
            for l in logs
            if l.level in (
                LogLevel.ERROR,
                LogLevel.CRITICAL
            )
        ]

        patterns = [
            r"([A-Za-z_]+\.[A-Za-z_]+DoesNotExist)",
            r"([A-Za-z_]+DoesNotExist)",
            r"([A-Za-z_]+Error)",
            r"([A-Za-z_]+Exception)",
        ]

        for msg in reversed(error_msgs):
            for pattern in patterns:
                match = re.search(pattern, msg)

                if match:
                    return (
                        f"{len(logs)} errors — "
                        f"{match.group(1)}"
                    )

        for msg in reversed(error_msgs):
            if "Internal Server Error" not in msg:
                return f"{len(logs)} errors — {msg[:120]}"

        return f"Incident: {len(logs)} anomalies detected"


    @staticmethod
    def _build_timeline(logs: list[LogEntry]) -> list[dict]:
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
    
    async def generate_gitlab_fix(
    self,
    incident_id,
):
        incident = await self._get_or_raise(
            incident_id
        )

        project = await self.db.get(
            Project,
            incident.project_id,
        )

        gitlab = GitLabService(
            project.gitlab_url,
            project.gitlab_token,
            project.gitlab_project_id,
        )

        files = gitlab.list_python_files()

        logs_text = "\n".join(
            [
                log.log_entry.message
                for log in incident.logs
                if log.log_entry
            ]
        )

        file_response = await self.ai.locate_file(
            logs_text,
            files,
        )

        file_data = json.loads(
            file_response
        )

        target_file = file_data["file"]

        source_code = gitlab.get_file(
            target_file
        )

        fix_response = await self.ai.generate_code_fix(
            logs_text,
            source_code,
        )

        fix_data = json.loads(
            fix_response
        )

        review_response = await self.ai.review_patch(
            fix_data["old_code"],
            fix_data["new_code"],
        )

        review_data = json.loads(
            review_response
        )

        if not review_data["safe"]:
            return {
                "success": False,
                "message": review_data["reason"],
            }

        incident.ai_fix_file = target_file

        incident.ai_fix_old_code = (
            fix_data["old_code"]
        )

        incident.ai_fix_new_code = (
            fix_data["new_code"]
        )

        incident.ai_fix_suggestion = (
            fix_data["explanation"]
        )

        await self.db.flush()

        return {
            "success": True,
            "file": target_file,
            "problem": fix_data["problem"],
            "explanation": fix_data["explanation"],
            "old_code": fix_data["old_code"],
            "new_code": fix_data["new_code"],
        }