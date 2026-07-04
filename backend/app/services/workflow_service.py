import asyncio
import uuid
from typing import Dict

from app.graph.builder import graph
from app.graph.state import ProjectState
from app.database import crud

# In-memory job store -- fast path for jobs from the current backend
# process. Every job is also persisted to SQLite (see app/database/) so
# job history and status survive a backend restart; get_job() falls back
# to the DB when a job_id isn't found here.
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
        "skip_agents": [],
    }
    crud.create_project(job_id, user_prompt)
    return job_id


def get_job(job_id: str) -> dict | None:
    job = _jobs.get(job_id)
    if job is not None:
        return job
    # Not in this process's memory -- e.g. the backend restarted since this
    # job ran. Fall back to what was persisted, and cache it so subsequent
    # lookups (and the websocket's polling loop) don't keep hitting SQLite.
    persisted = crud.get_project(job_id)
    if persisted is not None:
        _jobs[job_id] = persisted
    return persisted


def list_projects(limit: int = 50) -> list[dict]:
    """Summaries of past projects for a 'My Projects' view -- survives
    backend restarts since it reads from SQLite, not the in-memory dict."""
    return crud.list_projects(limit=limit)


def request_skip(job_id: str, agent_id: str) -> bool:
    """Mark an agent to be skipped the next time it would run.

    This just records the request in the in-memory job dict (_jobs).
    base_llm_agent.py's skip_check() reads this same dict directly at
    call time -- see its docstring for why that's necessary rather than
    routing this through LangGraph's state/checkpoint (aupdate_state()
    does not propagate to a continuous astream() call already in
    progress; verified empirically).

    Returns False if the job isn't known (caller should 404).
    """
    job = get_job(job_id)
    if job is None:
        return False
    skips = set(job.get("skip_agents") or [])
    skips.add(agent_id)
    job["skip_agents"] = list(skips)
    return True


async def run_workflow(job_id: str):
    """Run the LangGraph pipeline from start until it hits an interrupt or completes.

    Uses astream(..., stream_mode="values") instead of a single ainvoke() call.
    ainvoke() only returns once the ENTIRE segment finishes (e.g. PM AND
    Architect both complete before the approval_gate interrupt) — until then,
    _jobs[job_id] (the dict the websocket polls) never changes, so the UI
    looks completely frozen ("0 events") even while agents are actively
    working. Streaming yields the accumulated state after every node
    finishes, so we can update _jobs[job_id] — and therefore what the
    websocket sees — incrementally, agent by agent.
    """
    job = _jobs.get(job_id)
    if job is None:
        return

    try:
        initial_state: ProjectState = {
            "user_prompt": job["user_prompt"],
            "job_id": job_id,
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
            "skip_agents": job.get("skip_agents") or [],
        }

        config = {"configurable": {"thread_id": job_id}}

        async for state_chunk in graph.astream(initial_state, config=config, stream_mode="values"):
            # Merge in whatever has completed so far — the websocket loop
            # picks this up on its next 0.5s poll.
            _jobs[job_id].update(state_chunk)
            crud.update_project(job_id, _jobs[job_id])

        # Check if the graph is paused at an interrupt or has finished
        state = await graph.aget_state(config)

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

        crud.update_project(job_id, _jobs[job_id])

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        crud.update_project(job_id, _jobs[job_id])


async def resume_workflow(job_id: str, approved: bool, feedback: str):
    """Resume the paused LangGraph pipeline with user feedback and approval status.

    Same streaming fix as run_workflow() — see docstring there.
    """
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

        # 2. Resume execution (passing None tells LangGraph to continue from
        #    checkpoint), streaming node-by-node so progress is visible live.
        async for state_chunk in graph.astream(None, config=config, stream_mode="values"):
            _jobs[job_id].update(state_chunk)
            crud.update_project(job_id, _jobs[job_id])

        # Check if the graph is paused at another interrupt or has finished
        state = await graph.aget_state(config)

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

        crud.update_project(job_id, _jobs[job_id])

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        crud.update_project(job_id, _jobs[job_id])