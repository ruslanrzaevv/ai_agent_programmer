import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user, get_project_for_user
from app.db.session import get_db
from app.models.models import ExplainMode, Incident, IncidentLog, LogEntry, Project, User
from app.schemas.schemas import (
    AIResponse, ApplyFixRequest, AskAIRequest,
    ExplainRequest, IncidentOut, IncidentResolve, PaginatedResponse,
)
from app.services.ai_service import AIService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _svc(db: AsyncSession = Depends(get_db)) -> IncidentService:
    return IncidentService(db)


# ── List incidents for a project ──────────────────────────────────────────────

@router.get("/", response_model=PaginatedResponse)
async def list_incidents(
    project_id: uuid.UUID = Query(...),
    status_filter: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Incident).where(Incident.project_id == project_id)
    if status_filter:
        q = q.where(Incident.status == status_filter)
    if severity:
        q = q.where(Incident.severity == severity)
    q = q.order_by(desc(Incident.started_at))

    total = await db.scalar(q.with_only_columns(Incident.id).order_by(None))
    incidents = await db.scalars(q.limit(limit).offset(offset))

    return PaginatedResponse(
        items=[IncidentOut.model_validate(i) for i in incidents],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


# ── Get single incident ────────────────────────────────────────────────────────

@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incident = await _get_incident_for_user(incident_id, current_user.id, db)
    return IncidentOut.model_validate(incident)


# ── Acknowledge ────────────────────────────────────────────────────────────────

@router.post("/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: IncidentService = Depends(_svc),
    db: AsyncSession = Depends(get_db),
):
    await _get_incident_for_user(incident_id, current_user.id, db)
    incident = await svc.acknowledge(incident_id, current_user.id)
    await db.commit()
    return IncidentOut.model_validate(incident)


# ── Resolve ────────────────────────────────────────────────────────────────────

@router.post("/{incident_id}/resolve", response_model=IncidentOut)
async def resolve(
    incident_id: uuid.UUID,
    req: IncidentResolve,
    current_user: User = Depends(get_current_user),
    svc: IncidentService = Depends(_svc),
    db: AsyncSession = Depends(get_db),
):
    await _get_incident_for_user(incident_id, current_user.id, db)
    incident = await svc.resolve(incident_id)
    await db.commit()
    return IncidentOut.model_validate(incident)


# ── Incident Replay timeline ───────────────────────────────────────────────────

@router.get("/{incident_id}/replay", response_model=list[dict])
async def get_replay(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the full minute-by-minute timeline for Incident Replay.
    The frontend uses this to render the video-player-style scrubber.
    """
    incident = await _get_incident_for_user(incident_id, current_user.id, db)
    return incident.timeline or []


# ── AI: Re-explain with different mode ────────────────────────────────────────

@router.post("/{incident_id}/explain", response_model=AIResponse)
async def explain_incident(
    incident_id: uuid.UUID,
    req: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incident = await _get_incident_for_user(incident_id, current_user.id, db)

    # Return cached if available
    cached = {
        ExplainMode.JUNIOR: incident.ai_explanation_junior,
        ExplainMode.SENIOR: incident.ai_explanation_senior,
        ExplainMode.CEO: incident.ai_explanation_ceo,
    }.get(req.mode)

    if cached:
        return AIResponse(content=cached, mode=req.mode)

    # Generate on-demand
    logs = await _get_incident_logs(incident_id, db)
    ai = AIService()
    explanation = await ai.explain_incident(incident, logs, req.mode)

    # Cache it back
    if req.mode == ExplainMode.JUNIOR:
        incident.ai_explanation_junior = explanation
    elif req.mode == ExplainMode.SENIOR:
        incident.ai_explanation_senior = explanation
    else:
        incident.ai_explanation_ceo = explanation
    await db.commit()

    return AIResponse(content=explanation, mode=req.mode)


# ── AI: Free-form question ────────────────────────────────────────────────────

@router.post("/{incident_id}/ask", response_model=AIResponse)
async def ask_ai(
    incident_id: uuid.UUID,
    req: AskAIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incident = await _get_incident_for_user(incident_id, current_user.id, db)
    logs = await _get_incident_logs(incident_id, db, limit=20)
    ai = AIService()
    answer = await ai.ask(req.question, incident=incident, context_logs=logs)
    return AIResponse(content=answer)


# ── AI: Apply fix ─────────────────────────────────────────────────────────────

@router.post("/{incident_id}/apply-fix")
async def apply_fix(
    incident_id: uuid.UUID,
    req: ApplyFixRequest,
    current_user: User = Depends(get_current_user),
    svc: IncidentService = Depends(_svc),
    db: AsyncSession = Depends(get_db),
):
    await _get_incident_for_user(incident_id, current_user.id, db)
    result = await svc.apply_fix(incident_id, req.confirmed)
    if req.confirmed:
        await db.commit()
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_incident_for_user(
    incident_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Incident:
    incident = await db.scalar(
        select(Incident)
        .join(Project, Incident.project_id == Project.id)
        .where(Incident.id == incident_id, Project.owner_id == user_id)
    )
    if not incident:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


async def _get_incident_logs(
    incident_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 50,
) -> list[LogEntry]:
    rows = await db.scalars(
        select(LogEntry)
        .join(IncidentLog, LogEntry.id == IncidentLog.log_entry_id)
        .where(IncidentLog.incident_id == incident_id)
        .limit(limit)
    )
    return list(rows)