import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "suraksha_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "suraksha_secure_pass")
DB_NAME = os.getenv("DB_NAME", "suraksha_db")

# Assemble PostgreSQL connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

# Session Local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to provision database sessions for requests.
    Enforces cleanup of connection after request lifespans.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
