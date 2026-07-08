import os
import sys
import shutil
import subprocess
import socket
import logging
import time
import json
from pathlib import Path
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


def _pip_available(python_exe: str) -> bool:
    try:
        subprocess.run(
            [python_exe, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=15,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    except Exception:
        return False


def _ensure_pip(python_exe: str) -> None:
    """Bootstrap pip into this interpreter's environment if it's missing.

    Root cause this fixes: some Windows venvs (and some minimal Python
    installs) don't have pip available, producing "No module named pip"
    the moment we try `python -m pip install ...`. python's stdlib
    ensurepip module can install pip without needing pip itself already
    present, so we try that once before giving up.
    """
    proc = subprocess.run(
        [python_exe, "-m", "pip", "--version"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=15,
    )
    if proc.returncode == 0:
        return  # pip already works, nothing to do

    logger.warning("pip not available for %s, attempting to bootstrap via ensurepip...", python_exe)
    boot = subprocess.run(
        [python_exe, "-m", "ensurepip", "--upgrade"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60,
    )
    if boot.returncode != 0:
        raise RuntimeError(
            f"pip is unavailable for {python_exe} and could not be bootstrapped via ensurepip:\n"
            f"{boot.stdout[-1500:]}\n\n"
            f"Fix manually by running this yourself:\n  {python_exe} -m ensurepip --upgrade"
        )
    logger.info("pip successfully bootstrapped for %s", python_exe)


def _detect_backend_runtime(backend_path: str) -> str:
    """Detect what kind of backend was actually generated, instead of
    assuming Python -- previously this code unconditionally ran
    `pip install -r requirements.txt` and `uvicorn main:app` for every
    generated backend, which silently broke (or produced misleading
    errors) whenever the AI generated a Node.js/Express backend instead,
    since there's no requirements.txt or main:app to run in that case.
    """
    if os.path.exists(os.path.join(backend_path, "package.json")):
        return "node"
    if os.path.exists(os.path.join(backend_path, "requirements.txt")):
        return "python"
    return "unknown"


def _start_python_backend(python_exe: str, backend_path: str, port: int) -> subprocess.Popen:
    requirements = os.path.join(backend_path, "requirements.txt")
    if os.path.exists(requirements):
        _ensure_pip(python_exe)
        _run_blocking(
            [python_exe, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
            cwd=backend_path,
            timeout=_INSTALL_TIMEOUT_SECS,
        )

    # Detect the actual entry module instead of assuming main:app --
    # generated projects can name their entry file differently.
    entry_module = "main:app"
    for candidate in ("main.py", "app.py", "server.py"):
        if os.path.exists(os.path.join(backend_path, candidate)):
            entry_module = f"{Path(candidate).stem}:app"
            break

    logger.info(f"Starting Python preview backend on port {port} ({entry_module})...")
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", entry_module, "--port", str(port), "--host", "127.0.0.1"],
        cwd=backend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _start_node_backend(backend_path: str, port: int) -> subprocess.Popen:
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    node_cmd = "node.exe" if os.name == "nt" else "node"

    package_json = os.path.join(backend_path, "package.json")
    _run_blocking(
        [npm_cmd, "install", "--silent"],
        cwd=backend_path,
        timeout=_INSTALL_TIMEOUT_SECS,
    )

    # Prefer an npm "start" script if one is defined; otherwise fall back
    # to running the detected entry file directly with node.
    start_cmd = [npm_cmd, "start"]
    try:
        with open(package_json, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        if not (pkg.get("scripts") or {}).get("start"):
            entry_file = "index.js"
            for candidate in ("index.js", "server.js", "app.js"):
                if os.path.exists(os.path.join(backend_path, candidate)):
                    entry_file = candidate
                    break
            start_cmd = [node_cmd, entry_file]
    except (OSError, json.JSONDecodeError):
        pass

    logger.info(f"Starting Node.js preview backend on port {port} ({' '.join(start_cmd)})...")
    env = os.environ.copy()
    env["PORT"] = str(port)
    return subprocess.Popen(
        start_cmd,
        cwd=backend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
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
        # 1. Backend: detect Python vs Node.js and run the appropriate
        #    install/start commands -- previously this always assumed
        #    Python/pip/uvicorn regardless of what was actually generated.
        if os.path.exists(backend_path):
            runtime = _detect_backend_runtime(backend_path)
            if runtime == "python":
                python_exe = _resolve_python()
                backend_proc = _start_python_backend(python_exe, backend_path, backend_port)
            elif runtime == "node":
                backend_proc = _start_node_backend(backend_path, backend_port)
            else:
                logger.error(
                    "Backend for job %s has neither requirements.txt nor package.json -- "
                    "can't determine how to run it.", job_id,
                )

            if backend_proc is not None:
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