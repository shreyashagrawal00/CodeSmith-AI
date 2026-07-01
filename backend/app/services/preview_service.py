import os
import subprocess
import socket
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)

# Active preview processes: job_id -> { "backend_proc": Popen, "frontend_proc": Popen, "backend_port": int, "frontend_port": int }
_active_previews: Dict[str, dict] = {}

def get_free_port() -> int:
    """Find a free TCP port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_preview(job_id: str, project_dir: str) -> dict:
    """Start background processes for the generated backend and frontend apps."""
    if job_id in _active_previews:
        stop_preview(job_id)

    backend_port = get_free_port()
    frontend_port = get_free_port()

    backend_path = os.path.join(project_dir, "backend")
    frontend_path = os.path.join(project_dir, "frontend")

    backend_proc = None
    frontend_proc = None

    try:
        # 1. Start Backend if directory exists
        if os.path.exists(backend_path):
            # Check for virtual environment python or use system python
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            venv_python = os.path.join(os.path.dirname(base_dir), ".venv", "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                venv_python = "python"

            logger.info(f"Starting preview backend on port {backend_port}...")
            # Run uvicorn in project folder
            backend_proc = subprocess.Popen(
                [venv_python, "-m", "uvicorn", "main:app", "--port", str(backend_port), "--host", "127.0.0.1"],
                cwd=backend_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )

        # 2. Start Frontend if directory exists
        if os.path.exists(frontend_path):
            logger.info(f"Starting preview frontend on port {frontend_port}...")
            # Run npm run dev (or similar) or vite --port
            # We want to force Vite to run on the specific port without prompting
            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev", "--", "--port", str(frontend_port), "--host", "127.0.0.1", "--strictPort"],
                cwd=frontend_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )

        _active_previews[job_id] = {
            "backend_proc": backend_proc,
            "frontend_proc": frontend_proc,
            "backend_port": backend_port,
            "frontend_port": frontend_port,
            "timestamp": time.time()
        }

        return {
            "success": True,
            "backend_url": f"http://localhost:{backend_port}",
            "frontend_url": f"http://localhost:{frontend_port}"
        }

    except Exception as e:
        logger.error(f"Failed to start live preview for job {job_id}: {str(e)}")
        # Clean up any partially started processes
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
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
