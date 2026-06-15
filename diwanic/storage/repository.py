"""
Diwanic Repository
==================

Authoritative data-access layer for the Diwanic system.

Responsibility
--------------
- Wraps all SQLAlchemy queries behind clean, high-level methods.
- Enforces the *Postgres-as-Truth* contract: metadata is always
  hydrated from this module, never from the vector store.
- Provides both synchronous and asynchronous variants of every
  lookup method.

Thread-safety
--------------
- The synchronous repository expects an injected ``Session``.
- The asynchronous repository expects an ``AsyncSession``.
- Neither class holds global mutable state; instances are designed
  for request-scoped usage.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from diwanic.models import Poet, Poem, Verse


class DiwanicRepository:
    """
    Synchronous repository for Diwanic metadata lookups.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_poem_by_id(self, poem_id: str) -> Optional[Poem]:
        """Return a Poem ORM object by its UUID."""
        return self.db.query(Poem).filter(Poem.id == poem_id).first()

    def get_verse(self, poem_id: str, verse_index: int) -> Optional[Verse]:
        """Return a single Verse ORM object identified by poem + index."""
        return self.db.query(Verse).filter(
            Verse.poem_id == poem_id,
            Verse.verse_index == verse_index,
        ).first()

    def get_verses_by_poem_id(self, poem_id: str) -> List[Verse]:
        """Return all verses belonging to a poem, ordered by verse_index."""
        return self.db.query(Verse).filter(
            Verse.poem_id == poem_id
        ).order_by(Verse.verse_index).all()

    def get_poet_by_id(self, poet_id: str) -> Optional[Poet]:
        """Return a Poet ORM object by its UUID."""
        return self.db.query(Poet).filter(Poet.id == poet_id).first()

    def search_poems_by_keyword(self, keyword: str, limit: int = 10) -> List[Poem]:
        """Full-text keyword search over poem text."""
        return self.db.query(Poem).filter(
            Poem.searchable_text.ilike(f"%{keyword}%")
        ).limit(limit).all()


class AsyncDiwanicRepository:
    """
    Asynchronous repository for Diwanic metadata lookups.
    
    Used by the async search pipeline and FastAPI routes to avoid
    blocking the event loop.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_poem_by_id(self, poem_id: str) -> Optional[Poem]:
        """Return a Poem ORM object by its UUID (async)."""
        result = await self.db.execute(
            select(Poem).where(Poem.id == poem_id)
        )
        return result.scalars().first()

    async def get_verse(self, poem_id: str, verse_index: int) -> Optional[Verse]:
        """Return a single Verse ORM object identified by poem + index (async)."""
        result = await self.db.execute(
            select(Verse).where(
                Verse.poem_id == poem_id,
                Verse.verse_index == verse_index,
            )
        )
        return result.scalars().first()

    async def get_verses_by_poem_id(self, poem_id: str) -> List[Verse]:
        """Return all verses belonging to a poem, ordered by verse_index (async)."""
        result = await self.db.execute(
            select(Verse).where(Verse.poem_id == poem_id)
            .order_by(Verse.verse_index)
        )
        return list(result.scalars().all())

    async def get_poet_by_id(self, poet_id: str) -> Optional[Poet]:
        """Return a Poet ORM object by its UUID (async)."""
        result = await self.db.execute(
            select(Poet).where(Poet.id == poet_id)
        )
        return result.scalars().first()

    async def search_poems_by_keyword(self, keyword: str, limit: int = 10) -> List[Poem]:
        """Full-text keyword search over poem text (async)."""
        result = await self.db.execute(
            select(Poem).where(
                Poem.searchable_text.ilike(f"%{keyword}%")
            ).limit(limit)
        )
        return list(result.scalars().all())
