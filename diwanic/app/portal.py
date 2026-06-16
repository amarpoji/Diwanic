"""Portal bridge: thin wrappers that connect the Gradio Discovery UI to the real Diwanic engine."""

from typing import List, Dict, Any

# Core engine objects (same instances used elsewhere in the project)
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal

router = IntentRouter()
engine = HybridSearchEngineV2()
repo = DiwanicRepository(SessionLocal())


def perform_semantic_search(
    query: str,
    era: str = "all",
    poet: str = "all",
) -> List[Dict[str, Any]]:
    """
    Execute a search through the existing pipeline and return UI-ready dicts.
    Each dict contains: id, title, snippet, category, poet, era, score.
    """
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
                "category": getattr(r, "source", ""),  # SearchResult has no 'mood' field
                "poet": getattr(r, "poet", ""),
                "era": getattr(r, "era", ""),
                "score": float(getattr(r, "score", 0.0)),
            }
        )
    return feed


def get_poem_detail(poem_id: str) -> Dict[str, Any]:
    """
    Fetch the full poem payload for the detail modal by querying the ORM.
    Returns keys: title, full_text, poet, era, bio, category, insight, similar_ids, tts_path.
    """
    poem = repo.get_poem_by_id(poem_id)
    if not poem:
        return {}

    # Poet info comes from the relationship
    poet = poem.poet
    poet_name = poet.name_ar if poet else ""
    poet_era = poet.era if poet else ""
    poet_bio = poet.bio_ar if poet else ""
    poem_category = poem.category or ""

    # Similar poems: keyword search with same poet name, exclude current poem
    similar = []
    try:
        candidates = repo.search_poems_by_keyword(poet_name, limit=6)
        for c in candidates:
            if str(c.id) != poem_id:
                similar.append(str(c.id))
            if len(similar) >= 5:
                break
    except Exception:
        pass

    # TTS generation from the poem text
    tts_path = generate_tts_audio(poem.original_text)

    return {
        "title": poem.title,
        "full_text": poem.original_text,
        "poet": poet_name,
        "era": poet_era,
        "bio": poet_bio,
        "category": poem_category,
        "insight": f"التصنيف: {poem_category} | القافية: {poem.rhyme or 'غير محدد'} | البحر: {poem.meter or 'غير محدد'}",
        "similar_ids": similar,
        "tts_path": tts_path,
    }


def generate_tts_audio(text: str) -> str | None:
    """
    Generate an Arabic TTS file via gTTS. Returns the absolute path or None.
    """
    if not text:
        return None
    try:
        from gtts import gTTS
        import tempfile
        import os

        output_path = os.path.join(tempfile.gettempdir(), "diwanic_tts.mp3")
        tts = gTTS(text=text, lang="ar", slow=False)
        tts.save(output_path)
        return output_path
    except Exception:
        return None


def get_poem_of_the_day() -> Dict[str, Any]:
    """
    Return a hard-coded poem for the hero banner.
    Replace with a real DB query later if desired.
    """
    return {
        "title": "هل غادر الشعراء من متردم",
        "first_two_lines": "من أعماق التاريخ: هل غادر الشعراء من متردم...",
        "poet": "عنترة بن شداد",
        "era": "الجاهلي",
        "category": "فخر",
    }