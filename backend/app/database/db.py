"""Database persistence for project/job history.
Locally falls back to SQLite; in production uses Neon PostgreSQL via DATABASE_URL.
Neon's connection pooler (PgBouncer) requires NullPool so SQLAlchemy does not
maintain its own connection pool on top of it.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
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

# Use NullPool for Neon/PgBouncer pooler URLs to avoid "prepared statement" errors.
_is_postgres = DATABASE_URL.startswith("postgresql")
engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    poolclass=NullPool if _is_postgres else None,
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