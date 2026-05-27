"""
WebSocket connection manager.
Handles realtime push of logs, incidents, and metrics to connected clients.
Bridges Redis pub/sub → WebSocket.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict

from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger("ws_manager")


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by project_id.
    Each connection gets its own Redis subscriber task.
    """

    def __init__(self):
        # project_id -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        # ws -> task
        self._tasks: dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, project_id: str, user_id: str) -> None:
        await websocket.accept()
        self._connections[project_id].add(websocket)

        # Start Redis subscriber for this connection
        task = asyncio.create_task(
            self._redis_subscriber(websocket, project_id),
            name=f"ws:{user_id}:{project_id}",
        )
        self._tasks[websocket] = task

        logger.info("ws_connected", user_id=user_id, project_id=project_id)
        await websocket.send_json({"type": "connected", "project_id": project_id})

    async def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        self._connections[project_id].discard(websocket)
        if task := self._tasks.pop(websocket, None):
            task.cancel()
        logger.info("ws_disconnected", project_id=project_id)

    async def broadcast_to_project(self, project_id: str, message: dict) -> None:
        """Send a message to all clients subscribed to a project."""
        dead = set()
        for ws in self._connections.get(project_id, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[project_id].discard(ws)

    # ── Redis bridge ───────────────────────────────────────────────────────────

    async def _redis_subscriber(self, websocket: WebSocket, project_id: str) -> None:
        """Bridge Redis pub/sub → WebSocket for logs and incidents."""
        import redis.asyncio as aioredis
        from app.core.config import settings

        r = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        pubsub = r.pubsub()

        channels = [
            f"project:{project_id}:logs",
            f"project:{project_id}:incidents",
            f"project:{project_id}:metrics",
        ]
        await pubsub.subscribe(*channels)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except Exception as e:
                    logger.warning("ws_send_error", error=str(e))
                    break
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(*channels)
            await r.aclose()

    def stats(self) -> dict:
        return {
            "total_connections": sum(len(v) for v in self._connections.values()),
            "projects": {pid: len(conns) for pid, conns in self._connections.items()},
        }


ws_manager = ConnectionManager()