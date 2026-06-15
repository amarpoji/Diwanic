# Stage 6: Hybrid Search Integration

**Goal:** Implement hybrid retrieval by integrating Qdrant vector search into the V2 search engine to enable semantic Arabic poetry retrieval alongside metadata filters.

## Approach
- **Embedding Integration**: Added `sentence-transformers` to the search engine to generate query vectors on-the-fly.
- **Vector Retrieval**: Implemented `vector_search()` using Qdrant's `query_points` API.
- **Agentic Filtering**: Connected the `SearchPlan` filters (Poet, Era) directly to Qdrant's `Filter` system. This ensures the LLM can restrict semantic search to specific poets.
- **Hybrid Fusion**: Created a merge layer in `engine.search()` that combines semantic results from Qdrant with lexical results from PostgreSQL.

## Why this is a "Big Move"
1. **Meaning over Keywords**: Searching for "sadness" can now find poems about "tears" or "grief" even if the exact word "sad" isn't present.
2. **Metadata Strictness**: By applying LLM filters to the vector store, we solve the problem of "irrelevant high-similarity" results from other poets.
3. **Resilience**: If the keyword search fails (lexical gap), the vector search provides the answer. If the vector search is too broad, the keyword search provides precision.

## Challenges & Lessons
- **Schema Mismatch**: Discovered that V1 Qdrant data uses a flat payload (e.g., `poet`) while V2 logic initially expected a nested `metadata` object. Updated the search engine to handle the flat V1 schema to ensure backward compatibility.
- **Model Latency**: Large embedding models take ~45s to load in WSL. In production, we would keep the model warm in a long-lived service.

## Next Steps
- Implement **Reciprocal Rank Fusion (RRF)** for more scientific result merging.
- Upgrade to **Verse-level Retrieval** for laser-precise semantic matching.
