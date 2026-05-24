import subprocess
from config import DOCKER_CONTAINER_NAME

def restart_container():
    result = subprocess.run(
        ['docker', 'restart', DOCKER_CONTAINER_NAME],
        capture_output=True,
        text=True
    )
    
    return {
        'stdout': result.stdpout,
        'stderr': result.stderr,
    }