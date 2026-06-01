import json
import traceback
from fastapi import APIRouter, HTTPException

from app.services.wizard_service import (
    SetupWizardService,
)
from app.schemas.schemas import SetupWizardRequest, AnalyzeSetupRequest, ExplainRequest

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@router.post("/setup-wizard")
async def setup_wizard(req: SetupWizardRequest):

    service = SetupWizardService()

    result = await service.ask(
        req.category,
        req.message,
    )

    try:
        parsed = json.loads(result)

        return {
            "answer": parsed.get("answer", ""),
            "suggested_values": parsed.get(
                "suggested_values",
                {},
            ),
        }

    except Exception:
        return {
            "answer": result,
            "suggested_values": {},
        }
        
    
@router.post("/analyze-setup")
async def analyze_setup(
    req: AnalyzeSetupRequest,
):
    service = SetupWizardService()

    result = await service.analyze(
        req.form_data
    )
    
    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()


    try:
        parsed = json.loads(result)

        return parsed

    except Exception:

        return {
            "score": 0,
            "status": "critical",
            "summary": result,
            "issues": [],
            "recommendations": [],
        }
        
@router.post("/explain")
async def explain_issue(
    issue: str,
    level: str,
):
    service = SetupWizardService()

    response = service.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
Объясни проблему DevOps.

Проблема:
{issue}

Уровень:
{level}

Если level=junior:
объясняй максимально просто.

Если level=middle:
объясняй технически.

Если level=senior:
объясняй подробно с последствиями.

Верни только текст.
"""
    )

    return {
        "explanation": response.text
    }
    

@router.post("/explain")
async def explain_issue(
    req: ExplainRequest,
):
    service = SetupWizardService()

    response = service.client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"""
Объясни DevOps проблему.

Проблема:
{req.issue}

Уровень:
{req.level}

junior = максимально просто

middle = технически

senior = подробно для опытного DevOps инженера

Верни только текст.
"""
    )

    return {
        "explanation": response.text
    }