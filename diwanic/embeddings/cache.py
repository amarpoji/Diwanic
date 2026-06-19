"""
Embedding cache for Diwanic.

Stores pre-computed verse embeddings on disk using SHA-256 hashing of the verse text.
This avoids re-computing embeddings for verses that have already been processed,
significantly speeding up re-ingestion and reducing API costs.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional


class EmbeddingCache:
    """
    A simple file-based cache for verse embeddings.

    Stores embeddings in a JSON file at `cache_path`, keyed by the SHA-256
    hash of the verse text. On lookup, if the text was already embedded, the
    cached vector is returned immediately (no API call needed).
    """

    def __init__(self, cache_path: str = "data/embeddings/cache.json"):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[float]] = {}
        self._load()

    def _load(self) -> None:
        """Load cache from disk if it exists."""
        if self.cache_path.exists():
            with open(self.cache_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)

    def _save(self) -> None:
        """Persist cache to disk."""
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False)

    def _hash(self, text: str) -> str:
        """Return a SHA-256 hash of the text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """Return cached embedding if available, otherwise None."""
        key = self._hash(text)
        return self._cache.get(key)

    def set(self, text: str, embedding: List[float]) -> None:
        """Store an embedding in the cache and persist to disk."""
        key = self._hash(text)
        self._cache[key] = embedding
        self._save()

    def get_batch(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """Return a dict of {text: cached_embedding} for all texts."""
        return {text: self.get(text) for text in texts}

    def contains(self, text: str) -> bool:
        """Check if a text is already cached."""
        return self._hash(text) in self._cache

    def size(self) -> int:
        """Return the number of cached embeddings."""
        return len(self._cache)

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache = {}
        if self.cache_path.exists():
            self.cache_path.unlink()