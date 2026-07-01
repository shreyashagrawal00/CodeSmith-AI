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
        "task_queue": ["PM", "Architect", "DatabaseDesigner", "BackendEngineer", "FrontendEngineer", "Reviewer", "SecurityExpert", "QAEngineer", "BugFixer", "TechWriter", "DevOps"],
        "human_feedback": "",
        "approval_granted": False,
        "review_approved": False,
        "quality_score": 0.0,
        "correction_iterations": 0,
    }
    return job_id


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


async def run_workflow(job_id: str):
    """Run the LangGraph pipeline from start until it hits an interrupt or completes."""
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
            "task_queue": ["PM", "Architect", "DatabaseDesigner", "BackendEngineer", "FrontendEngineer", "Reviewer", "SecurityExpert", "QAEngineer", "BugFixer", "TechWriter", "DevOps"],
            "human_feedback": "",
            "approval_granted": False,
            "review_approved": False,
            "quality_score": 0.0,
            "correction_iterations": 0,
        }

        config = {"configurable": {"thread_id": job_id}}
        result = await graph.ainvoke(initial_state, config=config)

        # Check if the graph is paused at an interrupt or has finished
        state = await graph.aget_state(config)
        _jobs[job_id].update(result)

        if not state.next:
            # Finished completely
            _jobs[job_id]["status"] = "completed"
            
            # Post-completion tasks
            from app.services.project_service import write_project_files
            from app.services.report_service import zip_project
            from app.services.preview_service import start_preview
            
            project_dir = write_project_files(job_id, _jobs[job_id])
            zip_project(job_id)
            preview_res = start_preview(job_id, project_dir)
            if preview_res.get("success"):
                _jobs[job_id]["preview"] = {
                    "frontend_url": preview_res["frontend_url"],
                    "backend_url": preview_res["backend_url"]
                }
        else:
            # Paused at interrupt
            _jobs[job_id]["status"] = "paused"
            _jobs[job_id]["current_agent"] = state.next[0]

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)


async def resume_workflow(job_id: str, approved: bool, feedback: str):
    """Resume the paused LangGraph pipeline with user feedback and approval status."""
    job = _jobs.get(job_id)
    if job is None:
        return

    try:
        config = {"configurable": {"thread_id": job_id}}

        # 1. Update state with human feedback and approval
        await graph.aupdate_state(
            config,
            {
                "approval_granted": approved,
                "human_feedback": feedback,
                "status": "running"
            }
        )

        # Update local job status back to running for the UI
        _jobs[job_id]["status"] = "running"

        # 2. Resume execution (passing None tells LangGraph to continue from checkpoint)
        result = await graph.ainvoke(None, config=config)

        # Check if the graph is paused at another interrupt or has finished
        state = await graph.aget_state(config)
        _jobs[job_id].update(result)

        if not state.next:
            # Finished completely
            _jobs[job_id]["status"] = "completed"
            
            # Post-completion tasks
            from app.services.project_service import write_project_files
            from app.services.report_service import zip_project
            from app.services.preview_service import start_preview
            
            project_dir = write_project_files(job_id, _jobs[job_id])
            zip_project(job_id)
            preview_res = start_preview(job_id, project_dir)
            if preview_res.get("success"):
                _jobs[job_id]["preview"] = {
                    "frontend_url": preview_res["frontend_url"],
                    "backend_url": preview_res["backend_url"]
                }
        else:
            # Paused at another interrupt
            _jobs[job_id]["status"] = "paused"
            _jobs[job_id]["current_agent"] = state.next[0]

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
