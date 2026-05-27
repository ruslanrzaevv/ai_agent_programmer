import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_project_for_user
from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.session import get_db, AsyncSessionLocal
from app.models.models import LogEntry, LogLevel, LogSource, Project, User
from app.schemas.schemas import LogEntryOut, PaginatedResponse
from app.workers.monitoring_manager import monitoring_manager
from app.workers.ws_manager import ws_manager

logger = get_logger("api.logs")
router = APIRouter(tags=["logs & realtime"])


# ── Logs: query ───────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/logs", response_model=PaginatedResponse)
async def list_logs(
    project_id: uuid.UUID,
    level: str | None = Query(None),
    source: str | None = Query(None),
    container_name: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [LogEntry.project_id == project_id]

    if level:
        try:
            conditions.append(LogEntry.level == LogLevel(level))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Invalid level: {level}")
    if source:
        try:
            conditions.append(LogEntry.source == LogSource(source))
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Invalid source: {source}")
    if container_name:
        conditions.append(LogEntry.container_name == container_name)
    if search:
        conditions.append(LogEntry.message.ilike(f"%{search}%"))

    q = select(LogEntry).where(and_(*conditions)).order_by(desc(LogEntry.timestamp))
    logs = await db.scalars(q.limit(limit).offset(offset))

    return PaginatedResponse(
        items=[LogEntryOut.model_validate(l) for l in logs],
        total=0,  # count query omitted for perf; use X-Total-Count header in prod
        limit=limit,
        offset=offset,
    )


# ── WebSocket: realtime logs + incidents ──────────────────────────────────────

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
):
    """
    WebSocket endpoint for realtime monitoring.

    Connection URL: ws://api/ws/{project_id}?token=<jwt>

    Messages pushed from server:
    - {"type": "log", "data": {LogEntry}}
    - {"type": "incident_created", "incident_id": "...", "title": "...", "severity": "..."}
    - {"type": "metric", "data": {"cpu": 12.3, "memory_mb": 512}}
    - {"type": "connected", "project_id": "..."}

    Client can send:
    - {"type": "ping"} → server responds {"type": "pong"}
    """
    # Validate token from query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = decode_token(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Check project ownership
    async with AsyncSessionLocal() as db:
        project = await db.scalar(
            select(Project).where(
                Project.id == uuid.UUID(project_id),
                Project.owner_id == uuid.UUID(user_id),
            )
        )
        if not project:
            await websocket.close(code=4003, reason="Project not found")
            return

    await ws_manager.connect(websocket, project_id, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, project_id)


# ── GitLab webhook ────────────────────────────────────────────────────────────

@router.post("/webhooks/gitlab/{project_id}", status_code=status.HTTP_200_OK)
async def gitlab_webhook(
    project_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives GitLab webhook events.
    Configure in GitLab: Settings → Webhooks → URL: https://api/webhooks/gitlab/{project_id}
    Secret token: your project's gitlab_webhook_secret
    """
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")

    token = request.headers.get("X-Gitlab-Token")
    payload = await request.json()

    collector = monitoring_manager.get_gitlab_collector(str(project_id))
    if collector:
        try:
            await collector.process_webhook(payload, token)
        except ValueError as e:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e))
    else:
        logger.warning("no_gitlab_collector_for_webhook", project_id=str(project_id))

    return {"status": "received"}