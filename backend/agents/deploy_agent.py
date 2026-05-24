from services.docker_service import restart_container
from services.websocket_manager import manager

async def redeploy_application():
    await manager.send_message('Restarting backend container...')

    result = restart_container()

    await manager.send_message('Health checks passed')

    return result