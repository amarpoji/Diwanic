# Diwanic V2 — Architecture & End-to-End Flow

## Overview

This document maps every stage of the Diwanic V2 Hybrid Search pipeline to the
responsible files and folders in the project.  Use this as a navigation guide
when debugging or extending the system.

---

## The Flow Diagram

```
                              ┌─────────────────────┐
                              │  diwanic/app/ui.py   │
                              │   (Gradio Entry)     │
                              └──────────┬──────────┘
                                         │ Raw Query
                                         ▼
                              ┌─────────────────────┐
                              │ diwanic/search/      │
                              │   router.py          │
                              │   (IntentRouter)     │
                              │   + schemas/query.py │
                              │     (SearchPlan)     │
                              └──────────┬──────────┘
                                         │ Structured Plan
                                         ▼
                              ┌─────────────────────────────────┐
                              │ diwanic/search/engine.py         │
                              │   (HybridSearchEngineV2)         │
                              │   Orchestrates:                  │
                              │   1. Vector Search               │
                              │   2. Keyword Search              │
                              │   3. RRF Fusion                  │
                              │   4. Postgres Hydration          │
                              └──────┬──────────────┬────────────┘
                                     │              │
                     ┌───────────────┘              └───────────────┐
                     ▼                                               ▼
      ┌──────────────────────────┐              ┌──────────────────────────┐
      │ Vector Retrieval         │              │ Keyword Retrieval        │
      │                          │              │                          │
      │ diwanic/infrastructure/  │              │ diwanic/search/          │
      │   qdrant.py              │              │   engine.py              │
      │   (QdrantClient init)    │              │   (SQL scoring query)    │
      │                          │              │                          │
      │ diwanic/vectorstore/     │              │ diwanic/app/database.py  │
      │   verse_store.py         │              │   (Sync SessionLocal)    │
      │   (Qdrant collection)    │              │                          │
      └────────────┬─────────────┘              └────────────┬─────────────┘
                   │                                         │
                   └──────────────┬──────────────────────────┘
                                  ▼
                     ┌──────────────────────────┐
                     │ diwanic/search/rrf.py     │
                     │   Reciprocal Rank Fusion  │
                     │   Merges both result sets │
                     └──────────────┬───────────┘
                                    │ Fused list
                                    ▼
                     ┌──────────────────────────────┐
                     │ Postgres Hydration           │
                     │                              │
                     │ diwanic/storage/repository.py│
                     │   (DiwanicRepository)        │
                     │                              │
                     │ diwanic/models/              │
                     │   (Poet, Poem, Verse ORM)    │
                     │                              │
                     │ diwanic/app/database.py      │
                     │   (AsyncSession / Session)   │
                     └──────────────┬───────────────┘
                                    │ Hydrated results
                                    ▼
                     ┌──────────────────────────────┐
                     │ diwanic/schemas/search.py    │
                     │   (SearchResult,             │
                     │    SearchResponse)           │
                     └──────────────┬───────────────┘
                                    │ Final response
                                    ▼
                     ┌──────────────────────────────┐
                     │ diwanic/app/ui.py            │
                     │   (Display results)          │
                     └──────────────────────────────┘
```

---

## Stage 1: User Entry

| File / Folder | Role |
|---|---|
| `diwanic/app/ui.py` | Gradio interface. Entry point for the user. Captures the query string and calls `HybridSearchEngineV2.search()`. |

---

## Stage 2: Intent Routing (The Brain)

| File / Folder | Role |
|---|---|
| `diwanic/search/router.py` | `IntentRouter` class. Sends the query to a configured LLM (9Router) and parses the response into a `SearchPlan`. |
| `diwanic/schemas/query.py` | Pydantic models: `SearchPlan`, `ExtractedFilters`, `IntentResult`. Enforces a type-safe contract between the router and the engine. |
| `diwanic/core/config.py` | Provides `config.router.base_url`, `config.router.api_key`, and `config.router.model` for the router. |

---

## Stage 3: Hybrid Retrieval (Vector + Keyword)

| File / Folder | Role |
|---|---|
| `diwanic/search/engine.py` | `HybridSearchEngineV2` — the main orchestrator. Runs verse-level vector search, poem-level keyword search, and combines them via RRF. |
| `diwanic/infrastructure/qdrant.py` | Low-level `QdrantClient` initialization based on configuration. |
| `diwanic/vectorstore/verse_store.py` | Verse-level Qdrant collection manager. Contains collection name and upsert logic. |
| `diwanic/vectorstore/manager.py` | Poem-level Qdrant collection manager. |
| `diwanic/app/database.py` | Provides the synchronous `SessionLocal` and asynchronous `AsyncSessionLocal` engines for SQL operations. |

### Vector Search Sub-flow

1. `engine.py` calls `self.verse_search()` which:
   - Encodes the semantic query using `SentenceTransformer` (loaded in `__init__`)
   - Sends the embedding to Qdrant via `diwanic/infrastructure/qdrant.py`
   - Applies hard filters (poet name, era) on the Qdrant payload
   - Returns `SearchResult` objects from Qdrant's verse collection

### Keyword Search Sub-flow

1. `engine.py` calls `self.keyword_search()` which:
   - Extracts Arabic words from the semantic query
   - Builds a dynamic SQL query with per-word scoring
   - Applies hard filters (poet, era, category) via SQL `WHERE` clauses
   - Scores results by poet match + title match + term overlap
   - Returns `SearchResult` objects from Postgres

---

## Stage 4: Fusion (RRF)

| File / Folder | Role |
|---|---|
| `diwanic/search/rrf.py` | `reciprocal_rank_fusion()` function. Takes multiple ranked lists (verse vector results + poem keyword results), computes an RRF score for each unique document, and returns a single merged ranking. |

---

## Stage 5: Postgres-as-Truth Hydration

| File / Folder | Role |
|---|---|
| `diwanic/storage/repository.py` | `DiwanicRepository` (sync) and `AsyncDiwanicRepository` (async). Every method queries Postgres for the authoritative version of:
  - **Poems**: `get_poem_by_id()`
  - **Verses**: `get_verse()`, `get_verses_by_poem_id()`
  - **Poets**: `get_poet_by_id()`
  - **Search**: `search_poems_by_keyword()` |
| `diwanic/models/` | SQLAlchemy ORM models: `Poet`, `Poem`, `Verse`. Defines the database schema (columns, relationships, indexes). |
| `diwanic/app/database.py` | Engine and session factory. The `AsyncSessionLocal` is used by the async repository; `SessionLocal` is used by the sync repository. |

### Why Stage 5 Exists

The `engine` never trusts the Qdrant payload for metadata. After RRF fusion, every result ID is re-queried against Postgres to ensure:
- The title is the latest version
- The poet name and era are canonical
- The verse text is correct

This is the **Postgres-as-Truth** architectural contract.

---

## Stage 6: Response & Display

| File / Folder | Role |
|---|---|
| `diwanic/schemas/search.py` | `SearchResult` and `SearchResponse` Pydantic models. Defines the public response contract. |
| `diwanic/app/ui.py` | Formats the final `SearchResponse` for the Gradio UI. Displays poet name, poem title, verse text, and score in a user-friendly table. |

---

## Infrastructure & Support Layers

| File / Folder | Role |
|---|---|
| `diwanic/core/config.py` | Central Pydantic `Settings` class. Loads `.env` and provides type-safe access to all configuration values. |
| `diwanic/core/observability.py` | Logfire initialization. Instruments SQLAlchemy, HTTP (requests), and Pydantic validation. Provides end-to-end tracing (e.g., `ui_search` → `router_analyze_query` → `hybrid_search`). |
| `diwanic/utils/logger_util.py` | Logging setup helper. |
| `diwanic/utils/text_utils.py` | Arabic text normalization utilities. |
| `diwanic/utils/text_splitter.py` | Text chunking utilities. |
| `Dockerfile` | Multi-stage Docker build for the Python application. |
| `docker-compose.yml` | Orchestrates Postgres + Qdrant + Gradio App. |
| `Makefile` | Convenience commands: `make launch-ui`, `make docker-up`, etc. |
| `pyproject.toml` | Single source of truth for project metadata and dependencies. |

---

## Pipeline / Ingestion Layer (Scraping & Preprocessing)

These modules are used for data ingestion, not search. They are part of the
offline pipeline that builds the Postgres and Qdrant stores.

| File / Folder | Role |
|---|---|
| `diwanic/scraper/fetcher.py` | Downloads HTML from Aldiwan.net. |
| `diwanic/scraper/parser.py` | `PoemParser` — extracts poem title, poet, verses, and metadata from HTML. |
| `diwanic/scraper/pipeline.py` | Orchestrates fetch → parse → store. |
| `diwanic/scraper/models.py` | Scraper-specific data models. |
| `diwanic/preprocessing/cleaner.py` | Normalizes and cleans Arabic text. |
| `diwanic/preprocessing/pipeline.py` | Full preprocessing pipeline. |
| `diwanic/embeddings/generator.py` | Generates embeddings for poems/verses. |
| `diwanic/pipelines/flows/full_pipeline_flow.py` | Prefect flow for the full ingestion pipeline. |
| `diwanic/pipelines/tasks/` | Individual Prefect tasks (scrape, preprocess, embed, ingest). |

---

## Tests & Evaluation

| File / Folder | Role |
|---|---|
| `diwanic/search/evaluation.py` | `SearchEvaluator` — runs queries from a golden set against the live engine and computes MRR / Top-K recall. |
| `tests/golden_set.jsonl` | Golden set of known query → poem ID pairs used for regression testing. |

---

## Summary

| Layer | Key Directories / Files |
|---|---|
| **Entry** | `diwanic/app/ui.py` |
| **Routing** | `diwanic/search/router.py`, `diwanic/schemas/query.py` |
| **Engine** | `diwanic/search/engine.py` |
| **Vector** | `diwanic/infrastructure/qdrant.py`, `diwanic/vectorstore/verse_store.py` |
| **Keyword** | `diwanic/search/engine.py` (SQL scoring), `diwanic/app/database.py` |
| **Fusion** | `diwanic/search/rrf.py` |
| **Hydration** | `diwanic/storage/repository.py`, `diwanic/models/` |
| **Response** | `diwanic/schemas/search.py` |
| **Config** | `diwanic/core/config.py` |
| **Observability** | `diwanic/core/observability.py` |
| **Infrastructure** | `Dockerfile`, `docker-compose.yml`, `Makefile` |
