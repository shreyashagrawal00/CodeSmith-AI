"""SQLite-backed persistence for project/job history.

Why this exists: the generated project *files* were always written to disk
(backend/generated_projects/{job_id}/), so they already survived a backend
restart. But the job *metadata* (prompt, status, project name, timestamps)
only ever lived in workflow_service's in-memory `_jobs` dict -- so a restart
meant you could no longer list your past projects or look up their status,
even though the underlying files were still sitting right there.

This module gives that metadata a real home in SQLite so "my old projects"
persists across restarts.
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lives next to generated_projects/, at backend/codesmith.db
BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "codesmith.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI's threaded background tasks
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    from app.database import models  # noqa: F401 -- ensures the model is registered on Base
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Yield a session, ensuring it's always closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()