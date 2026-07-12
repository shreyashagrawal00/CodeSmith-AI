from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.workflow_service import create_job, get_job, run_workflow, resume_workflow, list_projects, request_skip

router = APIRouter()


class ProjectRequest(BaseModel):
    prompt: str


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


class SkipRequest(BaseModel):
    agent: str


@router.post("/generate")
async def generate_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """
    Start the multi-agent code generation pipeline.
    Returns a job_id to track progress.
    """
    job_id = create_job(request.prompt)
    background_tasks.add_task(run_workflow, job_id)
    return {"job_id": job_id, "status": "running", "message": "CodeSmith AI is building your project..."}


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Poll the current status and progress of a generation job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "current_agent": job.get("current_agent"),
        "log": job.get("log", []),
        "error": job.get("error"),
    }


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """Return the current generated state (requirements, architecture, code,
    docs, etc.) -- whatever sections have been produced so far.

    Deliberately allowed while status is "running", not just "completed"/
    "paused" -- this is what lets the frontend show each agent's output
    live as soon as it finishes, instead of only at pause points or the
    very end. Sections not yet produced are just empty dicts, which
    ProjectOutputViewer already renders as an empty state.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") == "failed":
        raise HTTPException(status_code=202, detail="Job failed before producing a result")
    return job


@router.post("/approve/{job_id}")
async def approve_job(job_id: str, request: ApprovalRequest, background_tasks: BackgroundTasks):
    """
    Submit approval or feedback for a paused job to resume the LangGraph workflow.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    background_tasks.add_task(resume_workflow, job_id, request.approved, request.feedback)
    return {"status": "resumed", "message": "Workflow resumed with feedback."}


@router.get("/download/{job_id}")
async def download_project(job_id: str):
    """Download the generated project as a ZIP archive."""
    from pathlib import Path
    zip_path = Path(__file__).resolve().parents[2] / "generated_projects" / f"{job_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Project archive not found. Job may not be complete yet.")
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"codesmith_project_{job_id[:8]}.zip",
    )


@router.post("/skip/{job_id}")
async def skip_agent(job_id: str, request: SkipRequest):
    """Mark an upcoming agent to be skipped for this job.

    Valid agent ids: PM, Architect, DatabaseDesigner, BackendEngineer,
    FrontendEngineer, Reviewer, SecurityExpert, QAEngineer, BugFixer,
    TechWriter, DevOps -- these match the ids used by the frontend's
    orchestration grid and the "agent" field in job.log entries.

    The skipped agent won't call any LLM -- it emits a "skipped by user"
    log entry and leaves its output section empty, so it can't retroactively
    un-skip an agent that already ran.
    """
    ok = request_skip(job_id, request.agent)
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "ok", "message": f"{request.agent} will be skipped when reached."}


@router.get("/projects")
async def get_projects(limit: int = 50):
    """List past projects (persisted in SQLite), newest first.

    This is what makes 'my old projects' survive a backend restart — the
    in-memory job dict is wiped on restart, but this reads from
    backend/codesmith.db instead.
    """
    return {"projects": list_projects(limit=limit)}


@router.post("/fix-job/{job_id}")
async def fix_job(job_id: str, request: ApprovalRequest, background_tasks: BackgroundTasks):
    """Trigger the BugFixer agent to run again on a completed job to address issues."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.services.workflow_service import run_manual_fix
    background_tasks.add_task(run_manual_fix, job_id, request.feedback)
    return {"status": "running", "message": "CodeSmith AI is running the BugFixer to patch the issues..."}