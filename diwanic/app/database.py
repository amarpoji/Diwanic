"""
Diwanic Database Module
========================
Provides both synchronous and asynchronous SQLAlchemy engine and session
factories for PostgreSQL.  The async engine is used by the search pipeline
to support high-concurrency access, while the sync engine remains available
for scripts and simple administrative tasks.

Contracts
---------
- The engine and session are created from ``config.database.url``.
- All async sessions use ``AsyncSession`` with ``asyncpg`` as the driver.
- Sync sessions use standard ``Session`` with ``psycopg2-binary``.
- Instrumentation is handled once by ``diwanic.core.observability``;
  no Logfire calls should be added here.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from diwanic.core.config import settings as config

# ──────────────────────────────────────────────
# Async engine (primary – used by search pipeline, FastAPI, etc.)
# ──────────────────────────────────────────────
# Replace "postgresql://" with "postgresql+asyncpg://" so SQLAlchemy
# uses the asyncpg driver.
_db_url = config.database.url.get_secret_value()
_async_db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://")

# Determine engine kwargs based on database type
_is_sqlite = _db_url.startswith("sqlite")

if _is_sqlite:
    # SQLite uses SingletonThreadPool, which doesn't support pool arguments
    _engine_kwargs = {"echo": False, "poolclass": sqlalchemy.pool.StaticPool}
    _async_engine_kwargs = {"echo": False}
else:
    _engine_kwargs = {"echo": False, "pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}
    _async_engine_kwargs = {"echo": False, "pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}

async_engine = create_async_engine(_async_db_url, **_async_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ──────────────────────────────────────────────
# Sync engine (fallback – for scripts / one-shot tasks)
# ──────────────────────────────────────────────
sync_engine = create_engine(_db_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

Base = declarative_base()


# ──────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────

async def get_async_db():
    """FastAPI dependency that yields an ``AsyncSession``.

    Yields
    ------
    AsyncSession
        A database session that is closed when the request completes.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


def get_db():
    """FastAPI dependency that yields a synchronous ``Session``.

    Yields
    ------
    Session
        A database session that is closed when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
