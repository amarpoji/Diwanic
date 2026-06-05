import logging
import psycopg2
from typing import List, Dict, Optional
from diwanic.core.config import config
from diwanic.vectorstore.manager import DiwanicVectorStore
from diwanic.embeddings.generator import PoemEmbedder
from diwanic.preprocessing.cleaner import ArabicCleaner

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    def __init__(self):
        """Initialize both search backends."""
        print("🤖 Loading Embedding Model (this may take a minute)...")
        self.embedder = PoemEmbedder()
        
        print("🔗 Connecting to Qdrant Cloud...")
        self.vector_store = DiwanicVectorStore()
        
        print("🧪 Initializing Arabic Cleaner...")
        self.cleaner = ArabicCleaner()
        
        # RRF parameter (k=60 is standard)
        self.k = 60
        print("✅ Search Engine Ready!")

    def _extract_poet_filter(self, query: str) -> tuple[str, Optional[str]]:
        """
        Intelligently extract poet names from the query.
        Returns: (cleaned_query, poet_name)
        """
        # Dictionary of aliases to database names
        poets = {
            "المتنبي": "المتنبي",
            "ابو نواس": "ابو نواس",
            "أبي نواس": "ابو نواس",
            "ابي نواس": "ابو نواس",
            "شوقي": "أحمد شوقي",
            "أحمد شوقي": "أحمد شوقي",
            "احمد شوقي": "أحمد شوقي",
            "الاصمعي": "الأصمعي",
            "الأصمعي": "الأصمعي",
            "الشافعي": "الشافعي",
            "الامام الشافعي": "الشافعي"
        }
        
        found_poet = None
        cleaned_query = query
        
        for alias, real_name in poets.items():
            if alias in query:
                found_poet = real_name
                # Remove the poet's name and common search prefixes
                cleaned_query = cleaned_query.replace(alias, "")
                prefixes = ["لأبي", "لابي", "للشاعر", "قصائد", "شعر"]
                for p in prefixes:
                    cleaned_query = cleaned_query.replace(p, "")
                break
                
        return cleaned_query.strip(), found_poet

    def semantic_search(self, query: str, limit: int = 10, poet_filter: str = None) -> List[Dict]:
        """Search by meaning (vector similarity)."""
        # Clean query
        cleaned_query = self.cleaner.clean_for_search(query)
        if not cleaned_query:
            cleaned_query = "شعر"
            
        # Generate embedding
        query_vector = self.embedder.embed_text(cleaned_query, prefix="query: ")
        
        # Build Qdrant filter
        filters = {}
        if poet_filter:
            filters["poet"] = poet_filter
            
        # Search Qdrant
        results = self.vector_store.search(query_vector, limit=limit, filters=filters)
        
        return [
            {
                "poem_id": r.payload.get("poem_id"),
                "title": r.payload.get("title"),
                "poet": r.payload.get("poet"),
                "era": r.payload.get("era"),
                "original_text": r.payload.get("original_text"),
                "vector_score": r.score
            }
            for r in results
        ]

    def keyword_search(self, query: str, limit: int = 10, poet_filter: str = None) -> List[Dict]:
        """Search by exact keywords (Postgres full-text search)."""
        cleaned_query = self.cleaner.clean_for_search(query)
        if not cleaned_query:
            cleaned_query = "شعر"
            
        conn = psycopg2.connect(config.DATABASE_URL)
        cur = conn.cursor()
        
        # Build SQL with optional poet filter
        if poet_filter:
            sql = """
                SELECT p.id, p.title, po.name_ar as poet, po.era, p.original_text,
                       ts_rank(p.fts_doc, plainto_tsquery('simple', %s)) as rank
                FROM poems p
                JOIN poets po ON p.poet_id = po.id
                WHERE p.fts_doc @@ plainto_tsquery('simple', %s)
                  AND po.name_ar = %s
                ORDER BY rank DESC
                LIMIT %s;
            """
            cur.execute(sql, (cleaned_query, cleaned_query, poet_filter, limit))
        else:
            sql = """
                SELECT p.id, p.title, po.name_ar as poet, po.era, p.original_text,
                       ts_rank(p.fts_doc, plainto_tsquery('simple', %s)) as rank
                FROM poems p
                JOIN poets po ON p.poet_id = po.id
                WHERE p.fts_doc @@ plainto_tsquery('simple', %s)
                ORDER BY rank DESC
                LIMIT %s;
            """
            cur.execute(sql, (cleaned_query, cleaned_query, limit))
            
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [
            {
                "poem_id": str(r[0]),
                "title": r[1],
                "poet": r[2],
                "era": r[3],
                "original_text": r[4],
                "keyword_score": float(r[5])
            }
            for r in rows
        ]

    def hybrid_search(self, query: str, limit: int = 10, vector_weight: float = 0.7, keyword_weight: float = 0.3) -> List[Dict]:
        """Combine semantic and keyword search using Reciprocal Rank Fusion."""
        logger.info(f"🔍 Hybrid search for: '{query}'")
        
        # 0. Extract filters (Agentic step)
        semantic_query, poet_filter = self._extract_poet_filter(query)
        if poet_filter:
            logger.info(f"📍 Detected poet filter: {poet_filter}")
        
        # 1. Get results from both backends
        vector_results = self.semantic_search(semantic_query, limit=limit * 2, poet_filter=poet_filter)
        keyword_results = self.keyword_search(semantic_query, limit=limit * 2, poet_filter=poet_filter)
        
        # 2. Build rank dictionaries (poem_id -> rank position)
        vector_ranks = {r["poem_id"]: rank for rank, r in enumerate(vector_results, 1)}
        keyword_ranks = {r["poem_id"]: rank for rank, r in enumerate(keyword_results, 1)}
        
        # Get all unique poem IDs
        all_poem_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())
        
        # Store metadata for final results
        all_metadata = {}
        for r in vector_results + keyword_results:
            all_metadata[r["poem_id"]] = r
            
        # 3. Apply Reciprocal Rank Fusion (RRF)
        fused_results = []
        for poem_id in all_poem_ids:
            score = 0
            if poem_id in vector_ranks:
                score += vector_weight / (self.k + vector_ranks[poem_id])
            if poem_id in keyword_ranks:
                score += keyword_weight / (self.k + keyword_ranks[poem_id])
                
            fused_results.append({
                "poem_id": poem_id,
                "score": score,
                "metadata": all_metadata[poem_id]
            })
            
        # 4. Sort and format final results
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        
        final_results = []
        for res in fused_results[:limit]:
            item = res["metadata"].copy()
            item["hybrid_score"] = res["score"]
            # Clean up component scores
            item.pop("vector_score", None)
            item.pop("keyword_score", None)
            final_results.append(item)
            
        return final_results
