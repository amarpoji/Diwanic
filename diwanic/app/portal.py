"""Portal bridge: thin wrappers that connect the Gradio Discovery UI to the real Diwanic engine."""

from typing import List, Dict, Any

# Core engine objects (same instances used elsewhere in the project)
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.storage.repository import DiwanicRepository

router = IntentRouter()
engine = HybridSearchEngineV2()
repo = DiwanicRepository()


def perform_semantic_search(
    query: str,
    era: str = "all",
    poet: str = "all",
) -> List[Dict[str, Any]]:
    """
    Execute a search through the existing pipeline and return UI-ready dicts.
    Each dict contains: id, title, snippet, mood, poet, era, score.
    """
    if not query or len(query.strip()) < 2:
        return []

    plan = router.analyze_query(query)
    results = engine.search(plan, limit=10)

    feed = []
    for r in results:
        feed.append(
            {
                "id": getattr(r, "poem_id", None),
                "title": getattr(r, "title", ""),
                "snippet": getattr(r, "original_text", "")[:150],
                "mood": getattr(r, "mood", ""),
                "poet": getattr(r, "poet", ""),
                "era": getattr(r, "era", ""),
                "score": float(getattr(r, "score", 0.0)),
            }
        )
    return feed


def get_poem_detail(poem_id: int) -> Dict[str, Any]:
    """
    Fetch the full poem payload for the detail modal.
    Expected keys: title, full_text, poet, era, bio, insight, similar_ids, tts_path.
    """
    poem = repo.get_by_id(poem_id)
    similar = repo.find_similar(poem_id, limit=5)
    tts_path = generate_tts_audio(poem.get("full_text", "") + " " + poem.get("first_lines", ""))

    return {
        "title": poem.get("title", ""),
        "full_text": poem.get("full_text", ""),
        "poet": poem.get("poet", ""),
        "era": poem.get("era", ""),
        "bio": poem.get("poet_bio", ""),
        "insight": poem.get("insights", ""),
        "similar_ids": [s.get("id") for s in similar],
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
    Return a hard-coded (or DB-backed) poem for the hero banner.
    Replace with a real query later if desired.
    """
    return {
        "title": "هل غادر الشعراء من متردم",
        "first_two_lines": "من أعماق التاريخ: هل غادر الشعراء من متردم...",
        "poet": "عنترة بن شداد",
        "era": "الجاهلي",
        "mood": "فخر",
    }