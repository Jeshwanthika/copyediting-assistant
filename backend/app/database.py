"""Database engine, session factory and declarative base."""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DEFAULT_DB_PATH, settings

DATABASE_URL = settings.resolved_database_url
IS_SQLITE = DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    # SQLite connections are shared across FastAPI worker threads.
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    """SQLite ignores foreign keys unless this is switched on per connection."""
    if IS_SQLITE:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create missing tables, then upgrade existing ones if a model gained columns."""
    import app.models  # noqa: F401  (registers the models on Base)

    Base.metadata.create_all(bind=engine)
    from app.migrations import run_migrations

    run_migrations(engine)  # upgrade databases created by an earlier stage
