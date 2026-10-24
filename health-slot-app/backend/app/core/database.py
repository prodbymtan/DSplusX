"""Database engine and session. Works with SQLite (default) or Postgres."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite: allow use across FastAPI's threads, and wait (instead of erroring)
    # if another request is mid-write.
    connect_args={"check_same_thread": False, "timeout": 15} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import db_models  # noqa: F401  (registers tables)

    Base.metadata.create_all(engine)


def reset_db() -> None:
    from app.models import db_models  # noqa: F401

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
