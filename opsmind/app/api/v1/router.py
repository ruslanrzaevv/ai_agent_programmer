from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, incidents, logs, projects, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(incidents.router)
api_router.include_router(logs.router)