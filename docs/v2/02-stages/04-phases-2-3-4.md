# Phase 2-4: Verse Indexing, RRF & Langfuse

This document tracks the integration of verse-level retrieval, hybrid ranking, and observability into the V2 engine.

## 🎯 Phase 2: Verse-Level Indexing
**Status:** Implementation Complete
**Goal:** Transition from poem-level to bayt-level (verse) retrieval.
- **Logic:** Each poem is split by the `...` shatr separator.
- **Vector Store:** New `verses` collection in Qdrant.
- **Metadata:** Each verse payload maintains a reference to the parent `poem_id`.
- **Script:** `scripts/index_verses.py` is ready for execution once Phase 1 data is processed.
- **V2 Integration:** New `verse_search()` method in `HybridSearchEngineV2`.

## 🧠 Phase 3: Reciprocal Rank Fusion (RRF)
**Status:** Implementation Complete
**Goal:** Interleave keyword and vector results using a mathematical ranking formula.
- **Logic:** `score = sum(1 / (k + rank))` with k=60.
- **Module:** `diwanic/search/rrf.py` implements the generic fusion logic.
- **V2 Integration:** `verse_search()` and `keyword_search()` results are processed through `reciprocal_rank_fusion()`.
- **Output:** Final results have `source="hybrid_rrf"` and computationally ranked scores.

## 👁️ Phase 4: Langfuse Observability
**Status:** Pending
**Goal:** Full tracing of the agentic RAG pipeline.
- **Tracking:** Monitor query intent confidence, retrieval scores, and latency.
- **Optimization:** Identify queries where the router fails or the engine returns low-quality results.
