"""SQLAlchemy engine + session for local SQLite.

Engine and session are created lazily so the module can be imported in
environments where SQLite/SQLAlchemy aren't available (e.g. Catalyst
serverless runtime with use_catalyst=True).
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def _init_engine():
    global _engine, _SessionLocal
    if _engine is not None:
        return
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .config import settings
    _engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {},
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@property
def _engine_prop(self):
    _init_engine()
    return _engine


def get_engine():
    _init_engine()
    return _engine


def get_session_local():
    _init_engine()
    return _SessionLocal


# Keep backward-compatible names as lazy proxies
class _EngineProxy:
    """Proxy so `engine` can be used at module level without triggering init."""
    def __getattr__(self, name):
        _init_engine()
        return getattr(_engine, name)

    @property
    def url(self):
        _init_engine()
        return _engine.url


class _SessionProxy:
    """Proxy so `SessionLocal()` works without triggering init at import."""
    def __call__(self, *a, **kw):
        _init_engine()
        return _SessionLocal(*a, **kw)

    def __getattr__(self, name):
        _init_engine()
        return getattr(_SessionLocal, name)


engine = _EngineProxy()
SessionLocal = _SessionProxy()


def get_db():
    _init_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate(eng):
    """Best-effort ALTER TABLE migrations for columns added after initial
    table creation."""
    import sqlite3
    real_engine = eng if not isinstance(eng, _EngineProxy) else get_engine()
    conn = sqlite3.connect(real_engine.url.database)
    migrations = [
        "ALTER TABLE evidence_documents ADD COLUMN remarks TEXT",
        "ALTER TABLE witnesses ADD COLUMN document_path VARCHAR(255)",
        "ALTER TABLE witnesses ADD COLUMN document_name VARCHAR(255)",
        "ALTER TABLE conversations ADD COLUMN case_id INTEGER REFERENCES cases(id)",
        "ALTER TABLE users ADD COLUMN subdivision VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN station VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN range_name VARCHAR(60)",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except Exception:
            pass
    conn.commit()
    conn.close()
