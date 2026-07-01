import subprocess
import logging
import os
import shutil

logger = logging.getLogger(__name__)

def run_command(command: str, cwd: str = None, timeout: int = 60) -> dict:
    """Execute a shell command safely in a specific working directory.

    Args:
        command: The shell command string to run.
        cwd: The working directory to run the command in.
        timeout: Timeout in seconds.

    Returns:
        dict: containing 'success', 'stdout', 'stderr', and 'exit_code'.
    """
    if not cwd:
        cwd = os.getcwd()
        
    os.makedirs(cwd, exist_ok=True)
    logger.info(f"Executing command: {command} in cwd: {cwd}")
    
    try:
        # Use shell=True for windows compatibility & running package/command binaries
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            timeout=timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {command}")
        return {
            "success": False,
            "stdout": e.stdout or "",
            "stderr": f"Error: Command timed out after {timeout} seconds.",
            "exit_code": -1
        }
    except Exception as e:
        logger.error(f"Failed to execute command: {command}. Error: {str(e)}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error: {str(e)}",
            "exit_code": -99
        }
