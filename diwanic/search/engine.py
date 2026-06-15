from typing import List, Optional

import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client import models
from sentence_transformers import SentenceTransformer
import logfire

from diwanic.core.config import settings as config
from diwanic.schemas.query import SearchPlan
from diwanic.schemas.search import SearchResult
from diwanic.app.database import SessionLocal


class HybridSearchEngineV2:
    """
    Hybrid search engine for Arabic poetry.

    Responsibility
    --------------
    Orchestrates the complete retrieval pipeline:
    1. **Verse-level vector search** (Qdrant) — high-precision verse matching.
    2. **Poem-level keyword search** (Postgres full-text) — recall for exact terms.
    3. **Reciprocal Rank Fusion (RRF)** — combines both result sets into a
       single ranked list.
    4. **Postgres hydration** — enriches every result with authoritative
       metadata from Postgres (Postgres-as-Truth contract).

    Threading / Async
    ------------------
    This class is synchronous.  Each ``__init__`` call opens a new DB session
    and loads the SentenceTransformer model.  For async usage, wrap the
    ``search`` call in ``asyncio.to_thread()``.

    Lifecycle
    ---------
    - ``__init__`` : Opens DB session and loads the embedding model.
    - ``search``   : Main entry point.
    - ``close``    : Must be called to release the DB connection.

    Configuration
    -------------
    Qdrant URL/API key and embedding model are read from
    ``config.qdrant`` and ``config.embedding``.
    """

    def __init__(self):
        self.db: Session = SessionLocal()
        # Initialize Qdrant client based on configuration
        if config.qdrant.url:
            self.qdrant = QdrantClient(
                url=config.qdrant.url,
                api_key=config.qdrant.api_key.get_secret_value(),
                timeout=60.0
            )
        else:
            self.qdrant = QdrantClient(
                host=config.qdrant.host,
                port=config.qdrant.port,
                timeout=60.0
            )
        self.collection_name = "poems"
        # Initialize embedding model (using the same one from V1 for consistency)
        self.model = SentenceTransformer('intfloat/multilingual-e5-small')

    def _normalize_arabic_name(self, text_value: Optional[str]) -> Optional[str]:
        """Normalize common Arabic name variants for metadata matching."""
        if not text_value:
            return None
        value = text_value.strip()
        # Normalize hamza/alef variants for metadata filters only
        value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        # Normalize common spacing issues
        value = re.sub(r"\s+", " ", value)
        return value

    def close(self):
        """Close DB session cleanly."""
        if self.db:
            self.db.close()

    def keyword_search(self, plan: SearchPlan, limit: int = 10) -> List[SearchResult]:
        """
        V2 Keyword Search with Improved Scoring.

        1. If hard filters (poet, era, etc.) are present, we prioritize them.
        2. Score individual keyword matches instead of full phrase.
        3. Rank poems by how many thematic words they contain.
        """
        import re

        # Extract individual Arabic words from the semantic query
        arabic_words = re.findall(r'[\u0600-\u06FF]+', plan.semantic_query)
        stop_words = {"في", "من", "على", "إلى", "عن", "ب", "ل", "ك", "و", "أن", "إن", "هذا", "هذه", "تعبر", "قصائد", "أبيات", "شعر"}
        filtered_words = [w for w in arabic_words if w not in stop_words and len(w) > 2]

        # Build the dynamic SQL with per-word scoring
        sql_base = """
            SELECT
                p.id AS poem_id,
                p.title,
                po.name_ar AS poet,
                po.era,
                p.original_text,
                p.searchable_text,
                0 AS match_score
            FROM poems p
            JOIN poets po ON po.id = p.poet_id
            WHERE 1=1
        """

        params = {"limit": limit}

        # Apply Hard Filters (Must match)
        has_hard_filters = False
        if plan.filters.poet_name:
            normalized_poet = self._normalize_arabic_name(plan.filters.poet_name)
            sql_base += " AND REPLACE(REPLACE(REPLACE(po.name_ar, 'أ', 'ا'), 'إ', 'ا'), 'آ', 'ا') ILIKE :poet_filter"
            params["poet_filter"] = f"%{normalized_poet}%"
            has_hard_filters = True

        if plan.filters.era:
            normalized_era = self._normalize_arabic_name(plan.filters.era)
            sql_base += " AND po.era ILIKE :era_filter"
            params["era_filter"] = f"%{normalized_era}%"
            has_hard_filters = True

        if plan.filters.category:
            normalized_cat = self._normalize_arabic_name(plan.filters.category)
            sql_base += " AND p.category ILIKE :cat_filter"
            params["cat_filter"] = f"%{normalized_cat}%"
            has_hard_filters = True

        # Build a score that rewards the poet match, title match, and term overlap.
        score_parts = ["0"]

        if plan.filters.poet_name:
            score_parts.append("CASE WHEN REPLACE(REPLACE(REPLACE(sub.poet, 'أ', 'ا'), 'إ', 'ا'), 'آ', 'ا') ILIKE :poet_score THEN 5 ELSE 0 END")
            params["poet_score"] = f"%{normalized_poet}%"

        if plan.filters.era:
            score_parts.append("CASE WHEN sub.era ILIKE :era_score THEN 1 ELSE 0 END")
            params["era_score"] = f"%{normalized_era}%"

        if plan.filters.category:
            score_parts.append("CASE WHEN sub.title ILIKE :cat_score OR sub.searchable_text ILIKE :cat_score THEN 1 ELSE 0 END")
            params["cat_score"] = f"%{normalized_cat}%"

        # If we have theme words, add them as individual scoring terms
        if filtered_words:
            for i, word in enumerate(filtered_words[:8]):  # Limit to 8 keywords to keep query sane
                key = f"word_{i}"
                params[key] = f"%{word}%"
                # Title match = 3 points, text match = 1 point
                score_parts.append(f"CASE WHEN sub.title ILIKE :{key} THEN 3 WHEN sub.searchable_text ILIKE :{key} THEN 1 ELSE 0 END")

        # Wrap the base query as a subquery and add scoring in the outer query
        sql = f"""
            SELECT *,
                ({' + '.join(score_parts)}) AS score_calc
            FROM (
                {sql_base}
            ) AS sub
            ORDER BY score_calc DESC, RANDOM() DESC LIMIT :limit
        """

        rows = self.db.execute(text(sql), params).mappings().all()

        results: List[SearchResult] = []
        for row in rows:
            results.append(
                SearchResult(
                    poem_id=str(row["poem_id"]),
                    title=row["title"],
                    poet=row["poet"],
                    era=row["era"],
                    original_text=row["original_text"],
                    searchable_text=row["searchable_text"],
                    score=float(row.get("score_calc", row.get("match_score", 0.0)) or 0.0),
                    source="keyword",
                )
            )

        return results

    def vector_search(self, plan: SearchPlan, limit: int = 10) -> List[SearchResult]:
        """
        Perform semantic search using Qdrant.
        Apply hard filters from the SearchPlan to the vector search.
        """

        # 1. Generate embedding for the semantic query
        # E5 models require 'query: ' prefix for queries
        query_text = f"query: {plan.semantic_query}"
        vector = self.model.encode(query_text).tolist()

        # 2. Build Qdrant filters based on SearchPlan
        q_filters = []

        if plan.filters.poet_name:
            # V1 Qdrant payload is flat: 'poet', not 'metadata.poet'
            q_filters.append(models.FieldCondition(
                key="poet",
                match=models.MatchValue(value=plan.filters.poet_name)
            ))

        if plan.filters.era:
            # V1 Qdrant payload is flat: 'era', not 'metadata.era'
            q_filters.append(models.FieldCondition(
                key="era",
                match=models.MatchValue(value=plan.filters.era)
            ))

        query_filter = models.Filter(must=q_filters) if q_filters else None

        # 3. Execute search
        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        results: List[SearchResult] = []
        for point in response.points:
            payload = point.payload
            # Note: V1 Qdrant payload is flat, not nested under 'metadata'
            results.append(
                SearchResult(
                    poem_id=str(payload.get("poem_id", point.id)),
                    title=payload.get("title", "Unknown Title"),
                    poet=payload.get("poet", "Unknown Poet"),
                    era=payload.get("era"),
                    original_text=payload.get("original_text", ""),
                    searchable_text=payload.get("searchable_text"),
                    score=float(point.score),
                    source="vector"
                )
            )

        return results

    def verse_search(self, plan: SearchPlan, limit: int = 10) -> List[SearchResult]:
        """
        Perform semantic search against the verse-level collection.
        This provides high-precision matching by finding the exact relevant bayt (verse).
        """
        from qdrant_client import models

        query_text = f"query: {plan.semantic_query}"
        vector = self.model.encode(query_text).tolist()

        q_filters = []
        if plan.filters.poet_name:
            q_filters.append(models.FieldCondition(
                key="poet",
                match=models.MatchValue(value=plan.filters.poet_name)
            ))

        if plan.filters.era:
            q_filters.append(models.FieldCondition(
                key="era",
                match=models.MatchValue(value=plan.filters.era)
            ))

        query_filter = models.Filter(must=q_filters) if q_filters else None

        response = self.qdrant.query_points(
            collection_name="verses",
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        results: List[SearchResult] = []
        for point in response.points:
            payload = point.payload
            results.append(
                SearchResult(
                    poem_id=str(payload.get("poem_id", "")),
                    title=payload.get("title", "Unknown Title"),
                    poet=payload.get("poet", "Unknown Poet"),
                    era=payload.get("era"),
                    original_text=payload.get("text", ""),
                    searchable_text=None,
                    score=float(point.score),
                    source="vector",
                    verse_index=payload.get("verse_index"),
                    match_type="verse"
                )
            )

        return results

    def search(self, plan: SearchPlan, limit: int = 10) -> List[SearchResult]:
        """
        V2 Hybrid Search: Combines Verse-level Vector and Poem-level Keyword retrieval.
        Merges results using Reciprocal Rank Fusion (RRF).
        Hydrates metadata from Postgres (Authoritative Source).
        """
        from diwanic.search.rrf import reciprocal_rank_fusion
        from diwanic.storage.repository import DiwanicRepository

        with logfire.span("hybrid_search", query=plan.semantic_query):
            # 1. Get results from both sources
            v_results = self.verse_search(plan, limit=limit)
            k_results = self.keyword_search(plan, limit=limit)

            # 2. Convert to dicts for RRF
            v_dicts = []
            for r in v_results:
                d = r.dict()
                # Stable ID for RRF: v_{poem_id}_{verse_index}
                d["id"] = f"v_{r.poem_id}_{r.verse_index}"
                v_dicts.append(d)

            k_dicts = []
            for r in k_results:
                d = r.dict()
                # Stable ID for RRF: k_{poem_id}
                d["id"] = f"k_{r.poem_id}"
                k_dicts.append(d)

            # 3. Apply RRF
            fused_dicts = reciprocal_rank_fusion([v_dicts, k_dicts], k=60)

            # 4. Normalize RRF scores to 0-1 scale
            max_score = max((d.get("rrf_score", 0.0) for d in fused_dicts), default=1.0)
            for d in fused_dicts:
                d["rrf_score"] = d.get("rrf_score", 0.0) / max_score

            # 5. Hydrate from Postgres (Authoritative Truth)
            repo = DiwanicRepository(self.db)
            final_results = []
            
            for d in fused_dicts:
                poem_id = d.get("poem_id")
                verse_idx = d.get("verse_index")
                
                # Fetch AUTHORITATIVE data from Postgres
                poem_obj = repo.get_poem_by_id(poem_id)
                
                if not poem_obj:
                    continue

                # Base metadata from Postgres
                hydrated = {
                    "poem_id": str(poem_obj.id),
                    "title": poem_obj.title,
                    "poet": poem_obj.poet.name_ar if poem_obj.poet else "Unknown",
                    "era": poem_obj.poet.era if poem_obj.poet else None,
                    "score": d.get("rrf_score", 0.0),
                    "source": "hybrid_rrf",
                }

                # Verse-specific hydration
                if verse_idx is not None:
                    # Find the specific verse in Postgres using Repository
                    verse_obj = repo.get_verse(poem_id, verse_idx)
                    if verse_obj:
                        hydrated.update({
                            "original_text": verse_obj.original_text,
                            "searchable_text": verse_obj.searchable_text,
                            "verse_index": verse_idx,
                            "match_type": "verse"
                        })
                    else:
                        # Fallback to poem text if verse not found in DB
                        hydrated.update({
                            "original_text": poem_obj.original_text,
                            "searchable_text": poem_obj.searchable_text,
                            "match_type": "poem"
                        })
                else:
                    # Poem-level match
                    hydrated.update({
                        "original_text": poem_obj.original_text,
                        "searchable_text": poem_obj.searchable_text,
                        "match_type": "poem"
                    })

                final_results.append(SearchResult(**hydrated))

                if len(final_results) >= limit:
                    break

            logfire.info("Search hydration complete", count=len(final_results))
            return final_results

    def health_check(self) -> dict:
        """Basic connectivity check for the engine."""
        return {
            "database": self.db is not None,
            "qdrant": self.qdrant is not None,
            "collection": self.collection_name,
        }
