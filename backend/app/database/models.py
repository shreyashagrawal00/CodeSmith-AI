"""SQLAlchemy models for persisted project/job history."""
from sqlalchemy import Column, String, Text, DateTime, Float, Integer
from sqlalchemy.sql import func

from app.database.db import Base


class Project(Base):
    """One row per generation job -- created when a job starts, updated as
    it progresses, and readable after a backend restart (unlike the old
    in-memory-only _jobs dict).
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)

    user_prompt = Column(Text, nullable=False)
    project_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    status = Column(String(32), nullable=False, default="running")  # running | paused | completed | failed
    current_agent = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)

    # Full job state (requirements, architecture, code, reports, live_log,
    # etc.) serialized as JSON text. SQLite has no native JSON column type,
    # so this is stored as TEXT and (de)serialized in crud.py.
    state_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())