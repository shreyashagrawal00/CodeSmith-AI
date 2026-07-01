import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.workflow_service import create_job, get_job, run_workflow, resume_workflow
from app.services.project_service import write_project_files
from app.services.report_service import zip_project

from app.services.preview_service import start_preview

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
    background_tasks.add_task(_run_and_save, job_id)
    return {"job_id": job_id, "status": "running", "message": "CodeSmith AI is building your project..."}


async def _run_and_save(job_id: str):
    """Background task: run the graph, write files, and zip the result."""
    await run_workflow(job_id)
    job = get_job(job_id)
    if job and job.get("status") == "completed":
        try:
            project_dir = write_project_files(job_id, job)
            zip_project(job_id)
            # Start background live preview
            preview_res = start_preview(job_id, project_dir)
            if preview_res.get("success"):
                job["preview"] = {
                    "frontend_url": preview_res["frontend_url"],
                    "backend_url": preview_res["backend_url"]
                }
        except Exception as e:
            job["status"] = "failed"
            job["error"] = f"File write or preview failed: {str(e)}"


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
