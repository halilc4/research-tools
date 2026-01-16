"""Database connection and session management."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

_DB_DIR = Path.home() / ".research-tools"
_DB_PATH = _DB_DIR / "data.db"

_engine = None


def get_db_path() -> Path:
    """Get the database file path, creating directory if needed."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


def get_engine():
    """Get or create the database engine (singleton)."""
    global _engine
    if _engine is None:
        db_path = get_db_path()
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return _engine


def init_db() -> None:
    """Initialize database - create all tables."""
    from .models import CacheEntry  # noqa: F401

    SQLModel.metadata.create_all(get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session as context manager."""
    session = Session(get_engine())
    try:
        yield session
    finally:
        session.close()


def create_session() -> Session:
    """Create a new session (caller responsible for closing)."""
    return Session(get_engine())
