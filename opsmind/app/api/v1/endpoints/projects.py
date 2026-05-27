import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_project_for_user
from app.db.session import get_db
from app.models.models import Project, User
from app.schemas.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from app.workers.monitoring_manager import monitoring_manager

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await db.scalars(
        select(Project).where(Project.owner_id == current_user.id, Project.is_active == True)  # noqa: E712
    )
    return list(projects)


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        owner_id=current_user.id,
        **req.model_dump(),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Start realtime monitoring immediately
    await monitoring_manager.start_project(project, current_user)

    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project: Project = Depends(get_project_for_user)):
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    req: ProjectUpdate,
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)

    # Restart monitoring with new config
    await monitoring_manager.restart_project(str(project.id))

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
):
    project.is_active = False
    await monitoring_manager.stop_project(str(project.id))
    await db.commit()


@router.post("/{project_id}/pause", response_model=ProjectOut)
async def pause_monitoring(
    project: Project = Depends(get_project_for_user),
    db: AsyncSession = Depends(get_db),
):
    project.monitoring_enabled = False
    await monitoring_manager.stop_project(str(project.id))
    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/resume", response_model=ProjectOut)
async def resume_monitoring(
    project: Project = Depends(get_project_for_user),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project.monitoring_enabled = True
    await db.commit()
    await monitoring_manager.start_project(project, current_user)
    await db.refresh(project)
    return project