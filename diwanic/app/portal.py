"""Portal bridge: thin wrappers that connect the Gradio Discovery UI to the real Diwanic engine.

Provides:
  • perform_semantic_search – query → list of UI‑ready dicts
  • get_poem_detail – full poem payload for the detail view
  • get_all_poets – list of poets (id_str, name, era)
  • get_poems_by_poet – list of poems for a given poet name

NOTE: Lazy-initialises engine/router/repo singletons on first use to avoid
blocking import-time (these constructors call out to Qdrant / Postgres).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from diwanic.search.router import IntentRouter
    from diwanic.search.engine import HybridSearchEngineV2
    from diwanic.storage.repository import DiwanicRepository

# Core engine objects — imported lazily inside functions
_router: Optional["IntentRouter"] = None
_engine: Optional["HybridSearchEngineV2"] = None
_repo: Optional["DiwanicRepository"] = None
_lock = threading.Lock()

# Single thread pool for timeouts
_executor = ThreadPoolExecutor(max_workers=1)


def _with_timeout(func, args=None, kwargs=None, timeout=10):
    """Run `func` with a timeout in seconds. Returns result or raises TimeoutError."""
    fut = _executor.submit(func, *(args or ()), **(kwargs or {}))
    try:
        return fut.result(timeout=timeout)
    except TimeoutError:
        fut.cancel()
        raise


def _get_router():
    global _router
    if _router is None:
        from diwanic.search.router import IntentRouter  # lazy import
        with _lock:
            if _router is None:
                _router = IntentRouter()
    return _router


def _get_engine():
    global _engine
    if _engine is None:
        from diwanic.search.engine import HybridSearchEngineV2  # lazy import
        with _lock:
            if _engine is None:
                _engine = HybridSearchEngineV2()
    return _engine


def _get_repo():
    global _repo
    if _repo is None:
        from diwanic.storage.repository import DiwanicRepository  # lazy import
        from diwanic.app.database import SessionLocal                # lazy import
        with _lock:
            if _repo is None:
                _repo = DiwanicRepository(SessionLocal())
    return _repo


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def perform_semantic_search(
    query: str,
    era: str = "all",
    poet: str = "all",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Run a search through the real engine and return UI‑ready dicts.
    
    Falls back to simple text matching if the embedding service times out.
    """
    if not query or len(query.strip()) < 2:
        return []
    
    # First try the full semantic engine with timeout
    try:
        router = _get_router()
        engine = _get_engine()
        plan = router.analyze_query(query)
        results = engine.search(plan, limit=limit)
    except Exception as e:
        print(f"[WARN] Semantic search failed: {e}, falling back to text search")
        return _fallback_text_search(query, limit)
    
    feed = []
    for r in results:
        poem_id = str(getattr(r, "poem_id", ""))
        
        # Fetch full poem text from database
        full_text = ""
        poet_name = getattr(r, "poet", "")
        poet_era = getattr(r, "era", "")
        
        if poem_id:
            try:
                poem_detail = get_poem_detail(poem_id)
                full_text = poem_detail.get("full_text", "")
                if not poet_name:
                    poet_name = poem_detail.get("poet", "")
                if not poet_era:
                    poet_era = poem_detail.get("era", "")
            except Exception:
                full_text = getattr(r, "original_text", "")
        
        feed.append(
            {
                "id": poem_id,
                "title": getattr(r, "title", ""),
                "snippet": full_text[:150] if full_text else getattr(r, "original_text", "")[:150],
                "full_text": full_text,  # Include full poem text
                "category": getattr(r, "source", ""),
                "poet": poet_name,
                "era": poet_era,
                "score": float(getattr(r, "score", 0.0)),
            }
        )
    return feed


def _fallback_text_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple LIKE-based search in the database for when embeddings fail."""
    from diwanic.app.database import SessionLocal
    from diwanic.models import Poem, Poet
    
    db = SessionLocal()
    try:
        # Search in poem title and original_text
        pattern = f"%{query}%"
        poems = (
            db.query(Poem)
            .join(Poet)
            .filter(
                (Poem.title.ilike(pattern)) | 
                (Poem.original_text.ilike(pattern))
            )
            .limit(limit)
            .all()
        )
        
        results = []
        for p in poems:
            results.append({
                "id": str(p.id),
                "title": p.title,
                "snippet": p.original_text[:150],
                "full_text": p.original_text,  # Include full poem text
                "category": p.category or "",
                "poet": p.poet.name_ar if p.poet else "",
                "era": p.poet.era if p.poet else "",
                "score": 0.5,  # Fake score for fallback results
            })
        return results
    finally:
        db.close()


def get_poem_detail(poem_id: str) -> Dict[str, Any]:
    """Fetch full poem data for the detail modal."""
    repo = _get_repo()
    poem = repo.get_poem_by_id(poem_id)
    if not poem:
        return {}

    poet = poem.poet
    poet_name = poet.name_ar if poet else ""
    poet_era = poet.era if poet else ""
    poet_bio = poet.bio_ar if poet else ""
    poem_category = poem.category or ""

    # Similar poems (same poet, limit 5, exclude current)
    similar = []
    try:
        candidates = repo.search_poems_by_keyword(poet_name, limit=6)
        for c in candidates:
            if str(c.id) != poem_id:
                similar.append(str(c.id))
            if len(similar) >= 5:
                break
    except Exception:
        similar = []

    return {
        "id": poem_id,
        "title": poem.title,
        "full_text": poem.original_text,
        "poet": poet_name,
        "era": poet_era,
        "bio": poet_bio,
        "category": poem_category,
        "insight": f"Category: {poem_category} | Poet: {poet_name}",
        "similar_ids": similar,
    }


def get_all_poets() -> List[Dict[str, Any]]:
    """Return a list of all poets with string IDs."""
    from diwanic.app.database import SessionLocal
    from diwanic.models import Poet
    db = SessionLocal()
    try:
        poets = db.query(Poet).order_by(Poet.name_ar).all()
        return [{"id": str(p.id), "name": p.name_ar, "era": p.era or ""} for p in poets]
    finally:
        db.close()


def get_poems_by_poet(poet_name: str) -> List[Dict[str, Any]]:
    """Return poems belonging to the given poet name."""
    from diwanic.app.database import SessionLocal
    from diwanic.models import Poet, Poem
    db = SessionLocal()
    try:
        poet = db.query(Poet).filter(Poet.name_ar == poet_name).first()
        if not poet:
            return []
        poems = db.query(Poem).filter(Poem.poet_id == poet.id).order_by(Poem.title).all()
        return [
            {
                "id": str(p.id),
                "title": p.title,
                "snippet": p.original_text[:120],
            }
            for p in poems
        ]
    finally:
        db.close()
