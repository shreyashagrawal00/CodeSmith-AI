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


def delete_project(job_id: str) -> bool:
    """Delete a project: removes the DB row, generated files, and the zip archive.
    Also removes the job from the in-memory cache if present.
    """
    if job_id in _jobs:
        del _jobs[job_id]
    return crud.delete_project(job_id)


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
            "compilation_errors": "",
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
            # NOTE: preview_res["success"] is (backend_up OR frontend_up),
            # so it can be True while only ONE of the two URL keys exists.
            # Bracket access on the other key raised a KeyError here that
            # silently flipped a successfully-completed job to
            # status="failed" -- the job actually finished fine, but the
            # crash destroyed that status and all visibility into why no
            # preview appeared. .get() + always recording whatever
            # succeeded/failed fixes both problems.
            _jobs[job_id]["preview"] = {
                "frontend_url": preview_res.get("frontend_url"),
                "backend_url": preview_res.get("backend_url"),
                "backend_error": preview_res.get("backend_error"),
                "frontend_error": preview_res.get("frontend_error"),
                "error": preview_res.get("error"),
            }
        else:
            # Paused at interrupt
            _jobs[job_id]["status"] = "paused"
            _jobs[job_id]["current_agent"] = state.next[0]

        crud.update_project(job_id, _jobs[job_id])

    except Exception as e:
        # Use .get() here to avoid a second KeyError if the job was somehow
        # removed from _jobs between the initial guard check and this handler.
        job = _jobs.get(job_id)
        if job is not None:
            job["status"] = "failed"
            job["error"] = str(e)
            crud.update_project(job_id, job)
        else:
            # Job is no longer tracked in memory — persist what we can
            # directly via CRUD so the failure isn't silently swallowed.
            crud.update_project(job_id, {"status": "failed", "error": str(e)})


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
            # NOTE: preview_res["success"] is (backend_up OR frontend_up),
            # so it can be True while only ONE of the two URL keys exists.
            # Bracket access on the other key raised a KeyError here that
            # silently flipped a successfully-completed job to
            # status="failed" -- the job actually finished fine, but the
            # crash destroyed that status and all visibility into why no
            # preview appeared. .get() + always recording whatever
            # succeeded/failed fixes both problems.
            _jobs[job_id]["preview"] = {
                "frontend_url": preview_res.get("frontend_url"),
                "backend_url": preview_res.get("backend_url"),
                "backend_error": preview_res.get("backend_error"),
                "frontend_error": preview_res.get("frontend_error"),
                "error": preview_res.get("error"),
            }
        else:
            # Paused at another interrupt
            _jobs[job_id]["status"] = "paused"
            _jobs[job_id]["current_agent"] = state.next[0]

        crud.update_project(job_id, _jobs[job_id])

    except Exception as e:
        job = _jobs.get(job_id)
        if job is not None:
            job["status"] = "failed"
            job["error"] = str(e)
            crud.update_project(job_id, job)
        else:
            crud.update_project(job_id, {"status": "failed", "error": str(e)})


async def run_manual_fix(job_id: str, feedback: str):
    """Manually trigger the BugFixer agent to patch code issues after workflow completion."""
    job = get_job(job_id)
    if job is None:
        return

    try:
        # Reset logs and status so UI shows active state
        job["status"] = "running"
        job["current_agent"] = "BugFixer"
        job["live_log"] = []
        crud.update_project(job_id, job)

        from app.agents.bugfix.agent import BugfixAgent

        # Construct ProjectState representation for the Agent invocation
        state: ProjectState = {
            "job_id": job_id,
            "backend_code": job.get("backend_code", {}),
            "frontend_code": job.get("frontend_code", {}),
            "review_report": job.get("review_report", {}),
            "security_report": job.get("security_report", {}),
            "compilation_errors": feedback,
            "correction_iterations": job.get("correction_iterations", 0),
            "log": job.get("log", []),
            "live_log": [],
        }

        # Run Bugfix Agent (blocks thread, run via to_thread)
        agent = BugfixAgent()
        result = await asyncio.to_thread(agent.run, state)

        # Merge the result back into our job representation
        # result contains backend_code, frontend_code, correction_iterations, bugfix_report
        job.update(result)
        job["status"] = "completed"

        # Write files, update zip and restart preview
        from app.services.project_service import write_project_files
        from app.services.report_service import zip_project
        from app.services.preview_service import start_preview

        project_dir = write_project_files(job_id, job)
        zip_project(job_id)
        preview_res = start_preview(job_id, project_dir)
        job["preview"] = {
            "frontend_url": preview_res.get("frontend_url"),
            "backend_url": preview_res.get("backend_url"),
            "backend_error": preview_res.get("backend_error"),
            "frontend_error": preview_res.get("frontend_error"),
            "error": preview_res.get("error"),
        }

        crud.update_project(job_id, job)

    except Exception as e:
        job = _jobs.get(job_id)
        if job is not None:
            job["status"] = "failed"
            job["error"] = str(e)
            crud.update_project(job_id, job)
        else:
            crud.update_project(job_id, {"status": "failed", "error": str(e)})