"""Portal bridge: thin wrappers that connect the Gradio Discovery UI to the real Diwanic engine.

Provides:
  • perform_semantic_search – query → list of UI‑ready dicts
  • get_poem_detail – full poem payload for the detail view
  • get_all_poets – list of poets (id_str, name, era)
  • get_poems_by_poet – list of poems for a given poet name
"""

from typing import List, Dict, Any

# Core engine objects
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal
from diwanic.models import Poet, Poem

# Engine / repo instances
router = IntentRouter()
engine = HybridSearchEngineV2()
repo = DiwanicRepository(SessionLocal())


def perform_semantic_search(
    query: str,
    era: str = "all",
    poet: str = "all",
) -> List[Dict[str, Any]]:
    """Run a search through the real engine and return UI‑ready dicts."""
    if not query or len(query.strip()) < 2:
        return []
    plan = router.analyze_query(query)
    results = engine.search(plan, limit=10)

    feed = []
    for r in results:
        feed.append(
            {
                "id": str(getattr(r, "poem_id", "")),
                "title": getattr(r, "title", ""),
                "snippet": getattr(r, "original_text", "")[:150],
                "category": getattr(r, "source", ""),
                "poet": getattr(r, "poet", ""),
                "era": getattr(r, "era", ""),
                "score": float(getattr(r, "score", 0.0)),
            }
        )
    return feed


def get_poem_detail(poem_id: str) -> Dict[str, Any]:
    """Fetch full poem data for the detail modal."""
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
    db = SessionLocal()
    try:
        poets = db.query(Poet).order_by(Poet.name_ar).all()
        return [{"id": str(p.id), "name": p.name_ar, "era": p.era or ""} for p in poets]
    finally:
        db.close()


def get_poems_by_poet(poet_name: str) -> List[Dict[str, Any]]:
    """Return poems belonging to the given poet name."""
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
