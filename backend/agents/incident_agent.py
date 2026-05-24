from services.elastic_service import get_logs
from services.gitlab_service import get_recent_commits
from services.gemini_service import analyze_incident
from services.websocket_manager import manager
from agents.reasoning import parse_ai_response

async def run_incident_investigation():
    await manager.send_message('Checking recent deploiment...')
    
    logs = get_logs()

    await manager.send_message('Analyze server logs...')
    
    commits = get_recent_commits()

    await manager.send_message('Reviewing Gitlab commits...')

    ai_response = analyze_incident(
        logs=str(logs),
        commits=str(commits)
    )
    
    await manager.send_message('AI reasoning complete...')

    parsed = parse_ai_response(ai_response)

    await manager.send_message('Root cause identified')

    return parsed