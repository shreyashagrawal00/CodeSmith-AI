import asyncio
import uuid
from typing import Dict

from app.graph.builder import graph
from app.graph.state import ProjectState

# In-memory job store
_jobs: Dict[str, dict] = {}


def create_job(user_prompt: str) -> str:
    """Create a new job, initialize state, and return the job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "user_prompt": user_prompt,
        "requirements": {},
        "architecture": {},
        "database_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "review_report": {},
        "security_report": {},
        "testing_report": {},
        "bugfix_report": {},
        "documentation": {},
        "deployment": {},
        "status": "running",
        "current_agent": "PM",
        "log": [],
        "live_log": [],
    }
    return job_id


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


async def run_workflow(job_id: str):
    """Run the full LangGraph pipeline for a given job."""
    job = _jobs.get(job_id)
    if job is None:
        return

    try:
        initial_state: ProjectState = {
            "user_prompt": job["user_prompt"],
            "requirements": {},
            "architecture": {},
            "database_schema": {},
            "backend_code": {},
            "frontend_code": {},
            "review_report": {},
            "security_report": {},
            "testing_report": {},
            "bugfix_report": {},
            "documentation": {},
            "deployment": {},
            "status": "running",
            "current_agent": "PM",
            "log": [],
            "live_log": [],
        }

        # Run the LangGraph pipeline asynchronously with state checkpointer config
        config = {"configurable": {"thread_id": job_id}}
        result = await graph.ainvoke(initial_state, config=config)

        # Update job store with final state
        _jobs[job_id].update(result)
        _jobs[job_id]["status"] = "completed"

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
