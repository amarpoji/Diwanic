"""
Diwanic Database Module
========================
Provides both synchronous and asynchronous SQLAlchemy engine and session
factories for PostgreSQL. Uses lazy initialization to support both SQLite
(in-memory for tests) and PostgreSQL (production).

Contracts
---------
- The engine and session are created from ``config.database.url``.
- All async sessions use ``AsyncSession`` with ``asyncpg`` as the driver.
- Sync sessions use standard ``Session`` with ``psycopg2-binary``.
- Engines are created lazily to support test environments.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from diwanic.core.config import settings as config
import threading

Base = declarative_base()

# Lazy initialization for engines
_async_engine = None
_sync_engine = None
_lock = threading.Lock()


def _get_engine_kwargs(url: str) -> dict:
    """Return appropriate engine kwargs based on database type."""
    is_sqlite = url.startswith("sqlite")
    if is_sqlite:
        return {"echo": False, "poolclass": sqlalchemy.pool.StaticPool}
    return {"echo": False, "pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}


def get_async_engine():
    """Lazily create and return the async engine."""
    global _async_engine
    if _async_engine is None:
        with _lock:
            if _async_engine is None:
                db_url = config.database.url.get_secret_value()
                async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
                kwargs = _get_engine_kwargs(db_url)
                _async_engine = create_async_engine(async_url, **kwargs)
    return _async_engine


def get_sync_engine():
    """Lazily create and return the sync engine."""
    global _sync_engine
    if _sync_engine is None:
        with _lock:
            if _sync_engine is None:
                db_url = config.database.url.get_secret_value()
                kwargs = _get_engine_kwargs(db_url)
                _sync_engine = create_engine(db_url, **kwargs)
    return _sync_engine


def get_async_session_maker():
    """Return an async session maker bound to the async engine."""
    return async_sessionmaker(bind=get_async_engine(), class_=AsyncSession, expire_on_commit=False)


def get_sync_session_maker():
    """Return a sync session maker bound to the sync engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_sync_engine())


# ──────────────────────────────────────────────
# Public helpers (for FastAPI dependency injection)
# ──────────────────────────────────────────────

async def get_async_db():
    """FastAPI dependency that yields an AsyncSession."""
    AsyncSessionLocal = get_async_session_maker()
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


def get_db():
    """FastAPI dependency that yields a synchronous Session."""
    SessionLocal = get_sync_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()