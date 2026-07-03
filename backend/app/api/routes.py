from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.workflow_service import create_job, get_job, run_workflow, resume_workflow, list_projects

router = APIRouter()


class ProjectRequest(BaseModel):
    prompt: str


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


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
    """Return the full generated state (requirements, architecture, code, docs, etc.)."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") not in ("completed", "paused"):
        raise HTTPException(status_code=202, detail="Job not completed or paused yet")
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


@router.get("/projects")
async def get_projects(limit: int = 50):
    """List past projects (persisted in SQLite), newest first.

    This is what makes 'my old projects' survive a backend restart — the
    in-memory job dict is wiped on restart, but this reads from
    backend/codesmith.db instead.
    """
    return {"projects": list_projects(limit=limit)}