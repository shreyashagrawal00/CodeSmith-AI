"""CRUD helpers for persisted project/job history.

These are called directly (not via FastAPI's Depends) since workflow_service
runs inside background tasks, not request handlers. Each function opens and
closes its own short-lived session.
"""
import json
import logging
from typing import Optional

from app.database.db import SessionLocal
from app.database.models import Project

logger = logging.getLogger(__name__)

# Keys from the in-memory job dict that get their own DB columns rather
# than being buried inside state_json, so they're queryable/listable
# without deserializing the whole blob.
_COLUMN_KEYS = {"status", "current_agent", "error", "quality_score"}


def create_project(job_id: str, user_prompt: str) -> None:
    db = SessionLocal()
    try:
        project = Project(
            job_id=job_id,
            user_prompt=user_prompt,
            status="running",
        )
        db.add(project)
        db.commit()
    except Exception:
        logger.exception("Failed to create persisted project row for job %s", job_id)
        db.rollback()
    finally:
        db.close()


def update_project(job_id: str, job_state: dict) -> None:
    """Persist a snapshot of the in-memory job dict to the DB row.

    Safe to call frequently (e.g. after every agent completes) -- on
    failure it logs and moves on rather than raising, since a persistence
    hiccup should never take down the actual generation pipeline.
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.job_id == job_id).first()
        if project is None:
            # Shouldn't normally happen (create_project runs first), but
            # don't lose data if it does.
            project = Project(job_id=job_id, user_prompt=job_state.get("user_prompt", ""))
            db.add(project)

        for key in _COLUMN_KEYS:
            if key in job_state:
                setattr(project, key, job_state[key])

        requirements = job_state.get("requirements") or {}
        if requirements.get("project_name"):
            project.project_name = requirements["project_name"]
        if requirements.get("description"):
            project.description = requirements["description"]

        try:
            project.state_json = json.dumps(job_state, default=str)
        except (TypeError, ValueError):
            logger.warning("Could not serialize full state for job %s; skipping state_json update", job_id)

        db.commit()
    except Exception:
        logger.exception("Failed to persist project row for job %s", job_id)
        db.rollback()
    finally:
        db.close()


def get_project(job_id: str) -> Optional[dict]:
    """Reconstruct a job dict from the DB -- used when a job isn't found in
    the in-memory cache (e.g. after a backend restart)."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.job_id == job_id).first()
        if project is None:
            return None

        state = {}
        if project.state_json:
            try:
                state = json.loads(project.state_json)
            except (TypeError, ValueError):
                logger.warning("Could not deserialize state_json for job %s", job_id)

        # DB columns take precedence over whatever was last baked into
        # state_json, since they're updated atomically alongside it.
        state["job_id"] = project.job_id
        state["user_prompt"] = project.user_prompt
        state["status"] = project.status
        state["current_agent"] = project.current_agent
        state["error"] = project.error
        state["quality_score"] = project.quality_score
        return state
    finally:
        db.close()


def list_projects(limit: int = 50) -> list[dict]:
    """Lightweight summaries for a "My Projects" list -- deliberately
    excludes state_json (which can be large) since callers just need
    enough to render a list and link into a specific project."""
    db = SessionLocal()
    try:
        projects = (
            db.query(Project)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "job_id": p.job_id,
                "project_name": p.project_name or "(untitled project)",
                "description": p.description,
                "user_prompt": p.user_prompt,
                "status": p.status,
                "current_agent": p.current_agent,
                "quality_score": p.quality_score,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ]
    finally:
        db.close()


def delete_project(job_id: str) -> bool:
    """Delete a project: removes the DB row, generated files on disk, and the
    ZIP archive.  Returns True if a row was found and deleted, False if not found.
    Never raises -- file-system errors are logged and ignored so the DB row is
    always cleaned up even if the files are already gone.
    """
    import shutil
    from pathlib import Path

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.job_id == job_id).first()
        if project is None:
            return False
        db.delete(project)
        db.commit()
    except Exception:
        logger.exception("Failed to delete project row for job %s", job_id)
        db.rollback()
        return False
    finally:
        db.close()

    # Best-effort cleanup of generated files
    base = Path(__file__).resolve().parents[2] / "generated_projects"
    project_dir = base / job_id
    zip_file = base / f"{job_id}.zip"
    try:
        if project_dir.exists():
            shutil.rmtree(project_dir)
    except Exception:
        logger.warning("Could not remove project directory %s", project_dir)
    try:
        if zip_file.exists():
            zip_file.unlink()
    except Exception:
        logger.warning("Could not remove zip file %s", zip_file)

    return True