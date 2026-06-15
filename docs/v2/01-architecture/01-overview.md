# V2 Architectural Overview

Diwanic V2 follows an **Agentic Search** pattern. The system doesn't just "query a database"; it "reasons about the intent" first.

---

## 🏗️ The 3-Layer Design

### 1. The Intent Layer (The "Brain")
- **File:** `v2/app/agents/router.py`
- **Tech:** LLM (via 9Router) + Pydantic.
- **Job:** Turn messy user text into a clean `SearchPlan`.
- **Key Logic:** Extract filters (poet, era) and generate an Arabic `semantic_query`.

### 2. The Retrieval Layer (The "Memory")
- **File:** `v2/app/search/engine.py`
- **Tech:** SQLAlchemy (Postgres) + Qdrant.
- **Job:** Execute the `SearchPlan`.
- **Key Logic:** Apply hard filters (SQL JOINs), calculate relevance scores, and merge results.

### 3. The API Layer (The "Skin")
- **File:** `v2/app/api/routes.py`
- **Tech:** FastAPI.
- **Job:** Receive HTTP requests and return JSON responses.
- **Key Logic:** Validate input, call the Brain, call the Memory, and format the output.

---

## 🔄 Data Flow (Sequence)

1. **Inbound:** User POSTs to `/api/v2/search`.
2. **Analysis:** `IntentRouter` asks 9Router: "What does this query mean?".
3. **Planning:** 9Router returns JSON → Router creates a `SearchPlan`.
4. **Execution:** `HybridSearchEngineV2` takes the Plan and queries Postgres.
5. **Normalization:** Database filters are normalized (Hamza/Alef) to ensure matches.
6. **Scoring:** Results are ranked by metadata + keyword overlap.
7. **Outbound:** `SearchResponse` is sent back as JSON.
