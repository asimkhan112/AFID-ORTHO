"""Database connection and session management (PostgreSQL)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from config import settings
import logging

logger = logging.getLogger(__name__)

# PostgreSQL engine with a real connection pool. `pool_pre_ping` validates a
# pooled connection before use so a DB restart doesn't surface stale-connection
# errors; `pool_recycle` proactively rotates long-lived connections.
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,          # persistent connections kept in the pool
    max_overflow=20,       # extra connections opened under load
    pool_timeout=30,       # seconds to wait for a free connection
    pool_recycle=1800,     # recycle connections older than 30 min
    pool_pre_ping=True,    # validate a connection before handing it out
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Ensure tables exist.

    Schema is owned by Alembic migrations (`alembic upgrade head`); this call is
    an idempotent safety net for fresh environments and is a no-op once the
    migration has run.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")
