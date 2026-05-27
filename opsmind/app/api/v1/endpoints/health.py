from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.db.redis import get_redis
from app.workers.monitoring_manager import monitoring_manager
from app.workers.ws_manager import ws_manager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    r = await get_redis()
    try:
        await r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": "ok" if redis_ok else "error",
        "monitoring": monitoring_manager.status(),
        "websockets": ws_manager.stats(),
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )