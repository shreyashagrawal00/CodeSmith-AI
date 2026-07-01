import logging
from app.tools.terminal_tool import run_command

logger = logging.getLogger(__name__)

def docker_build(image_name: str, build_context_path: str) -> dict:
    """Build a Docker image from a Dockerfile in the build context path.

    Returns:
        dict: success status and command outputs
    """
    res = run_command(f"docker build -t {image_name} .", cwd=build_context_path, timeout=300)
    return res

def docker_run_container(image_name: str, container_name: str, port_mapping: str) -> dict:
    """Run a Docker container in detached mode with port mapping."""
    cmd = f"docker run -d --name {container_name} -p {port_mapping} {image_name}"
    res = run_command(cmd, timeout=60)
    return res

def docker_stop_container(container_name: str) -> dict:
    """Stop and remove a running Docker container."""
    cmd = f"docker stop {container_name} && docker rm {container_name}"
    res = run_command(cmd, timeout=30)
    return res
