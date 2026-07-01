import os
import logging
from app.tools.terminal_tool import run_command

logger = logging.getLogger(__name__)

def execute_python_file(file_path: str, cwd: str = None) -> dict:
    """Execute a Python file and return stdout/stderr."""
    # Use python executable from active virtual environment if possible
    # Otherwise fallback to system 'python'
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Check if .venv/Scripts/python.exe exists in root or backend
    venv_python = os.path.join(os.path.dirname(base_dir), ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"
        
    cmd = f'"{venv_python}" "{file_path}"'
    return run_command(cmd, cwd=cwd)

def execute_vitest(frontend_path: str) -> dict:
    """Execute npm test suite inside the frontend directory."""
    return run_command("npm test -- --run", cwd=frontend_path)

def execute_pytest(backend_path: str) -> dict:
    """Execute pytest suite inside the backend directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    venv_pytest = os.path.join(os.path.dirname(base_dir), ".venv", "Scripts", "pytest.exe")
    if not os.path.exists(venv_pytest):
        venv_pytest = "pytest"
        
    cmd = f'"{venv_pytest}"'
    return run_command(cmd, cwd=backend_path)
