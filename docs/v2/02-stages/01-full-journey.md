# V2 Stages: The Journey from Brain to Results

This document tracks the step-by-step development of the Diwanic V2 pipeline.

---

## Stage 1: The Foundation (Config & Database)
**Goal:** Move from raw SQL scripts to a professional SQLAlchemy ORM foundation.

### Approach
- Created `v2/core/config.py` to handle all environment variables.
- Implemented `v2/app/database.py` to manage SQLAlchemy engine and sessions.
- Defined `v2/app/models/base.py` with SQLAlchemy classes for `Poet`, `Poem`, and `Verse`.

---

## Stage 2: The Contract (Pydantic Schemas)
**Goal:** Define exactly what a "Search Plan" looks like so the LLM and the Engine speak the same language.

### Approach
- Split the schema into `IntentResult` (understanding) and `SearchPlan` (instructions).
- Defined `SearchResult` and `SearchResponse` to ensure the API always returns predictable JSON.

---

## Stage 3: The Brain (9Router Intent Router)
**Goal:** Use an LLM to understand what the user wants before touching the database.

### Approach
- Integrated **9Router Proxy** to manage local LLM connections.
- Built `IntentRouter.analyze_query()` to convert natural language into a structured `SearchPlan`.
- Switched to **Raw JSON Prompting** for better stability (see [Decision 01](../04-decisions/01-raw-json-over-instructor.md)).

---

## Stage 4: The Engine (Hybrid Search Engine V2)
**Goal:** Execute the search plan and rank results.

### Approach
- Created `HybridSearchEngineV2` as a clean wrapper for DB and Qdrant.
- Implemented **Filter-First Fallback** logic to handle Arabic poetry nuances.
- Added **Per-Word Scoring** to replace strict sentence matching.

---

## Stage 5: The Interface (FastAPI Layer)
**Goal:** Expose the V2 system to the world.

### Approach
- Built `/api/v2/search` as a POST endpoint.
- Verified end-to-end flow: `HTTP -> Router -> Engine -> HTTP`.
- Implemented **In-Process Testing** to prove the pipeline works before server deployment.
