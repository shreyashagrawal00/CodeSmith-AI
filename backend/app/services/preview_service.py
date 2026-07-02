import os
import sys
import shutil
import subprocess
import socket
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Active preview processes: job_id -> { "backend_proc": Popen, "frontend_proc": Popen, "backend_port": int, "frontend_port": int }
_active_previews: Dict[str, dict] = {}

# How long to wait for each dependency-install step and each server to come up.
_INSTALL_TIMEOUT_SECS = 180
_PORT_WAIT_TIMEOUT_SECS = 30
_PORT_WAIT_POLL_INTERVAL = 0.5


def get_free_port() -> int:
    """Find a free TCP port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _resolve_python() -> str:
    """Return a python executable that actually exists on this machine.

    Prefers the interpreter currently running this process (guaranteed to
    exist), falling back to python3/python on PATH. The previous
    implementation only looked for a Windows-style .venv\\Scripts\\python.exe
    and fell back to the bare "python" command, which does not exist on most
    Linux/macOS systems (it's "python3" there) — so the backend preview
    process silently failed to spawn.
    """
    if sys.executable:
        return sys.executable
    for candidate in ("python3", "python"):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("No python interpreter found on PATH.")


def _wait_for_port(host: str, port: int, timeout: float) -> bool:
    """Poll until something is listening on host:port, or timeout elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(_PORT_WAIT_POLL_INTERVAL)
    return False


def _run_blocking(cmd: list, cwd: str, timeout: int) -> None:
    """Run a setup command (pip install / npm install) to completion.

    Raises with the captured output on failure so callers get an actionable
    error instead of a silently-broken preview.
    """
    logger.info("Running setup command in %s: %s", cwd, " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({' '.join(cmd)}) in {cwd}:\n{proc.stdout[-2000:]}"
        )


def start_preview(job_id: str, project_dir: str) -> dict:
    """Install dependencies, start the generated backend/frontend, and only
    report success once each server is actually accepting connections.
    """
    if job_id in _active_previews:
        stop_preview(job_id)

    backend_port = get_free_port()
    frontend_port = get_free_port()

    backend_path = os.path.join(project_dir, "backend")
    frontend_path = os.path.join(project_dir, "frontend")

    backend_proc: Optional[subprocess.Popen] = None
    frontend_proc: Optional[subprocess.Popen] = None
    backend_up = False
    frontend_up = False

    try:
        python_exe = _resolve_python()

        # 1. Backend: install deps, then start uvicorn, then wait for the port.
        if os.path.exists(backend_path):
            requirements = os.path.join(backend_path, "requirements.txt")
            if os.path.exists(requirements):
                _run_blocking(
                    [python_exe, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages", "--quiet"],
                    cwd=backend_path,
                    timeout=_INSTALL_TIMEOUT_SECS,
                )

            logger.info(f"Starting preview backend on port {backend_port}...")
            backend_proc = subprocess.Popen(
                [python_exe, "-m", "uvicorn", "main:app", "--port", str(backend_port), "--host", "127.0.0.1"],
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            backend_up = _wait_for_port("127.0.0.1", backend_port, _PORT_WAIT_TIMEOUT_SECS)
            if not backend_up:
                logger.error(
                    "Preview backend for job %s did not come up on port %d in time.",
                    job_id, backend_port,
                )

        # 2. Frontend: install deps, then start the dev server, then wait for the port.
        if os.path.exists(frontend_path):
            package_json = os.path.join(frontend_path, "package.json")
            if os.path.exists(package_json):
                npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
                _run_blocking(
                    [npm_cmd, "install", "--silent"],
                    cwd=frontend_path,
                    timeout=_INSTALL_TIMEOUT_SECS,
                )

            logger.info(f"Starting preview frontend on port {frontend_port}...")
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev", "--", "--port", str(frontend_port), "--host", "127.0.0.1", "--strictPort"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            frontend_up = _wait_for_port("127.0.0.1", frontend_port, _PORT_WAIT_TIMEOUT_SECS)
            if not frontend_up:
                logger.error(
                    "Preview frontend for job %s did not come up on port %d in time.",
                    job_id, frontend_port,
                )

        _active_previews[job_id] = {
            "backend_proc": backend_proc,
            "frontend_proc": frontend_proc,
            "backend_port": backend_port,
            "frontend_port": frontend_port,
            "timestamp": time.time()
        }

        # Only report success for the pieces that actually came up.
        result = {"success": backend_up or frontend_up}
        if backend_up:
            result["backend_url"] = f"http://localhost:{backend_port}"
        if frontend_up:
            result["frontend_url"] = f"http://localhost:{frontend_port}"
        if not backend_up and os.path.exists(backend_path):
            result["backend_error"] = "Backend preview server failed to start in time."
        if not frontend_up and os.path.exists(frontend_path):
            result["frontend_error"] = "Frontend preview server failed to start in time."
        return result

    except Exception as e:
        logger.error(f"Failed to start live preview for job {job_id}: {str(e)}")
        # Clean up any partially started processes
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        _active_previews.pop(job_id, None)
        return {"success": False, "error": str(e)}

def stop_preview(job_id: str):
    """Stop the background processes for the given job_id."""
    preview = _active_previews.pop(job_id, None)
    if not preview:
        return

    logger.info(f"Stopping live preview for job {job_id}...")
    
    # Terminate backend process
    b_proc = preview.get("backend_proc")
    if b_proc:
        try:
            b_proc.terminate()
            b_proc.wait(timeout=2)
        except Exception:
            pass

    # Terminate frontend process
    f_proc = preview.get("frontend_proc")
    if f_proc:
        try:
            f_proc.terminate()
            f_proc.wait(timeout=2)
        except Exception:
            pass
            
    logger.info(f"Live preview for job {job_id} stopped.")