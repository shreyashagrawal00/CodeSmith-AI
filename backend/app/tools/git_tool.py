import logging
from app.tools.terminal_tool import run_command

logger = logging.getLogger(__name__)

def git_init(repo_path: str) -> str:
    """Initialize a new Git repository at repo_path."""
    res = run_command("git init", cwd=repo_path)
    if not res["success"]:
        raise RuntimeError(f"git init failed: {res['stderr']}")
    return "Git repository initialized successfully."

def git_commit(repo_path: str, message: str) -> str:
    """Stage all changes and commit them with the given message."""
    # Run git add .
    res_add = run_command("git add .", cwd=repo_path)
    if not res_add["success"]:
        raise RuntimeError(f"git add failed: {res_add['stderr']}")
        
    # Run git commit
    res_commit = run_command(f'git commit -m "{message}"', cwd=repo_path)
    if not res_commit["success"]:
        # If nothing to commit, return success anyway
        if "nothing to commit" in res_commit["stdout"] or "nothing to commit" in res_commit["stderr"]:
            return "No changes to commit."
        raise RuntimeError(f"git commit failed: {res_commit['stderr']}")
        
    return f"Changes committed successfully: {message}"

def git_create_branch(repo_path: str, branch_name: str) -> str:
    """Create and checkout a new local git branch."""
    res = run_command(f"git checkout -b {branch_name}", cwd=repo_path)
    if not res["success"]:
        raise RuntimeError(f"Failed to create branch {branch_name}: {res['stderr']}")
    return f"Switched to a new branch '{branch_name}'."
