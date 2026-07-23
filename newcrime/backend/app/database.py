"""SQLAlchemy engine + session for local SQLite."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate(engine):
    """Best-effort ALTER TABLE migrations for columns added after initial
    table creation. SQLite's `CREATE TABLE IF NOT EXISTS` (used implicitly by
    Base.metadata.create_all) won't add new columns to an existing table, so
    we patch them in here. Safe to run repeatedly — errors (e.g. column
    already exists) are swallowed.
    """
    import sqlite3
    conn = sqlite3.connect(engine.url.database)
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
