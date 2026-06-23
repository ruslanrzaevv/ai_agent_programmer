from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/orbit", tags=["orbit"])


@router.get("/incident/{incident_id}")
async def get_orbit_analysis(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = IncidentService(db)

    incident = await svc._get_or_raise(
        incident_id
    )

    return {
        "root_cause": incident.orbit_root_cause,
        "affected_files": incident.orbit_affected_files,
        "affected_services": incident.orbit_affected_services,
        "risk_score": incident.orbit_risk_score,
        "blast_radius": incident.orbit_blast_radius,
        "definitions": incident.orbit_definitions,
        "imports": incident.orbit_imports,
    }