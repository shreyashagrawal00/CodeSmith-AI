"""SQLite-backed persistence for project/job history (local dev).
In production, set the DATABASE_URL environment variable to a PostgreSQL
connection string (e.g. from Neon: postgresql://user:pass@host/db?sslmode=require).
SQLAlchemy handles both drivers transparently -- no other code needs to change.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Connection URL ---
# Production: set DATABASE_URL in your Render environment variables.
# Local dev:  falls back to the SQLite file next to generated_projects/.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_SQLITE_FALLBACK = f"sqlite:///{_BACKEND_DIR / 'codesmith.db'}"
DATABASE_URL = os.environ.get("DATABASE_URL", _SQLITE_FALLBACK)

# Neon (and most cloud Postgres providers) give URLs starting with
# "postgres://" but SQLAlchemy requires "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL doesn't accept that arg.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
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