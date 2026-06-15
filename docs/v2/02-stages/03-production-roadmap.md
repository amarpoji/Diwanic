# Phase 1-4 Production Roadmap

This document outlines the multi-phase roadmap to transform Diwanic V2 into a high-scale, production-ready retrieval system.

## 📚 Phase 1: Corpus Expansion
**Status:** In Progress
**Goal:** Reach 500+ poems across major historical and modern poets.
- **Improved Scraper:** Fixed link extraction logic to reliably discover poems from poet category pages.
- **Target Poets:** Al-Mutanabbi, Abu Nuwas, Ahmad Shawqi, Al-Shafi'i, and more.
- **Storage:** Data is being saved to `data/raw/poems_expanded.jsonl` for downstream ingestion.

## 🎯 Phase 2: Verse-Level Indexing
**Status:** Planning/Infrastructure Ready
**Goal:** Transition from poem-level to bayt-level (verse) retrieval.
- **Logic:** Each poem is split by the `...` shatr separator.
- **Vector Store:** New `verses` collection in Qdrant.
- **Metadata:** Each verse payload maintains a reference to the parent `poem_id`.
- **Script:** `scripts/index_verses.py` is ready for execution once Phase 1 data is processed.

## 🧠 Phase 3: Reciprocal Rank Fusion (RRF)
**Status:** Implementation Ready
**Goal:** Interleave keyword and vector results using a mathematical ranking formula.
- **Logic:** `score = sum(1 / (k + rank))`
- **Module:** `diwanic/search/rrf.py` implements the generic fusion logic.
- **Integration:** To be wired into `HybridSearchEngineV2`.

## 👁️ Phase 4: Langfuse Observability
**Status:** Pending
**Goal:** Full tracing of the agentic RAG pipeline.
- **Tracking:** Monitor query intent confidence, retrieval scores, and latency.
- **Optimization:** Identify queries where the router fails or the engine returns low-quality results.
