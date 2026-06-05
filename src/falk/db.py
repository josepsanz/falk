"""Shared database engine and session factory.

A single engine is built lazily from the configured database URI and reused by
both the telemetry collector and the web API. SQLite pragmas mirror the Alembic
setup (foreign keys on) and add WAL plus a busy timeout so the API can read
while the cron telemetry job writes.
"""

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import database_uri

_SQLITE_BUSY_TIMEOUT_MS = 5000

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _configure_sqlite(dbapi_connection: object, _: object) -> None:
    """Apply per-connection SQLite pragmas for concurrency and integrity."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS}")
    cursor.close()


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine, _session_factory
    if _engine is None:
        uri = database_uri()
        _engine = create_engine(uri, future=True)
        if _engine.dialect.name == "sqlite":
            event.listen(_engine, "connect", _configure_sqlite)
        _session_factory = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def session_factory() -> sessionmaker[Session]:
    """Return the session factory bound to the shared engine."""
    get_engine()
    assert _session_factory is not None
    return _session_factory
