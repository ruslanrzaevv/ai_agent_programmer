from fastapi import APIRouter

from agents.incident_agent import run_incident_investigation
from agents.deploy_agent import redeploy_application

from models.incident_models import ApproveFixRequest

from services.gitlab_service import (
    create_branch,
    create_commit,
    create_merge_request
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.post("/investigate")
async def investigate_incident():

    result = await run_incident_investigation()

    return {
        "status": "investigation_complete",
        "data": result
    }


@router.post("/approve-fix")
async def approve_fix(data: ApproveFixRequest):

    branch_name = "ai-auto-fix"

    create_branch(branch_name)

    commit = create_commit(
        branch=branch_name,
        commit_message=data.commit_message,
        file_path=data.file_path,
        content=data.new_code
    )

    mr = create_merge_request(branch_name)

    deploy_result = await redeploy_application()

    return {
        "status": "success",
        "commit": commit,
        "merge_request": mr,
        "deploy": deploy_result
    }