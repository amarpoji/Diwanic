# 🗺️ Diwanic — Project Flow & Source of Truth
Last Updated: 2026-06-03

This document tracks the end-to-end data flow and the files responsible for each stage.

---

## 🌊 1. Data Pipeline (Version 1.0 - Current: Basic RAG)

All 7 stages below are fully functional but are "Dumb" — they don't understand user intent.

| Stage | Status | File / Tool |
| :--- | :--- | :--- |
| 1. Scrape | ✅ Done | `diwanic/scraper/pipeline.py` |
| 2. Clean | ✅ Done | `diwanic/preprocessing/cleaner.py` |
| 3. Database (Supabase) | ✅ Done | `diwanic/storage/db_manager.py` |
| 4. Embed (E5-small) | ✅ Done | `diwanic/embeddings/generator.py` |
| 5. Qdrant Cloud | ✅ Done | `diwanic/vectorstore/manager.py` |
| 6. Hybrid Search (RRF) | ✅ Done | `diwanic/search/engine.py` |
| 7. Web API (FastAPI) | ✅ Done | `diwanic/api/main.py` |

### Version 2.0: Agentic RAG (Planned)

This is the upgrade we researched from the `production-agentic-rag-course` repo and the Substack article. It adds a "Brain" (LLM) that understands user intent.

| V2.0 Stage | What it adds | New Tech/Skill |
| :--- | :--- | :--- |
| **8. LLM Router** | Parses "Cari puisi Abu Nawas" → `{poet: "ابو نواس", theme: "شعر"}` | `instructor`, `pydantic`, Prompt Engineering |
| **9. Re-ranker** | A second smarter model that re-checks results and discards irrelevant ones | `sentence-transformers` (Cross-Encoder) |
| **10. Query Expansion** | LLM translates "homesick" → "الحنين + الشوق + الوجد" (3 queries instead of 1) | API Integration |
| **11. Guardrails** | "I don't know" when results are weak | Confidence Scoring |
| **12. Langfuse** | Tracks every search step (latency, cost, success rate) | Langfuse SDK |
| **13. Telegram/Gradio** | Chat interface instead of raw JSON | `python-telegram-bot` / `gradio` |

---

## 🎮 2. Executive Scripts (The "Buttons")

| Script | Purpose | Status |
| :--- | :--- | :--- |
| `scripts/run_full_pipeline.py` | **Master Pipeline**: Scrape → Clean → Embed | ✅ Working |
| `scripts/scrape_all.py` | **Stage 1 Only**: Scrape poets from config | ✅ Working |
| `scripts/preprocess_data.py` | **Stage 2 Only**: Clean raw poems | ✅ Working |
| `scripts/ingest_to_db.py` | **Stage 3 Only**: Upload processed data to Supabase | ✅ Complete (21 poems) |
| `scripts/generate_embeddings.py` | **Stage 4 Only**: Generate vectors | ✅ Working |
| `scripts/load_to_qdrant.py` | **Stage 5 Only**: Upload embeddings to Qdrant Cloud | ✅ Complete (21 vectors) |
| `scripts/search.py` | **Stage 6 Only**: CLI Hybrid Search Tool | ✅ Working |
| `diwanic/api/main.py` | **Stage 7 Only**: Web API Server | ✅ Working |
| `scripts/discover_poet.py` | **Utility**: Find slug/name/era from Aldiwan URL | ✅ Working |
| `scripts/add_poet.py` | **Utility**: Add poet to `poets.yaml` | ✅ Working |

---

## 🛠️ 3. Environment Config (`.env`)

Every file above uses this config heart:
- `SCRAPER_DELAY`: Timing between web requests.
- `DATABASE_URL`: Your Supabase connection string. ✅ Set
- `QDRANT_URL`: Your Qdrant Cloud URL. ✅ Set
- `QDRANT_API_KEY`: Your Qdrant API key. ✅ Set

---

## 📂 4. Project Blueprint

```
diwanic/
├── diwanic/                    # THE KITCHEN (Classes & Logic)
│   ├── __init__.py
│   ├── core/                   # Config, Logger
│   │   ├── config.py           # .env loader
│   │   └── logger.py           # Logging utility
│   ├── scraper/                # Stage 1: Scraping
│   │   ├── fetcher.py          # HTTP requests + retry
│   │   ├── parser.py           # HTML → Poem data
│   │   ├── pipeline.py         # Batch scraping logic
│   │   └── models.py           # Poem dataclass (schema)
│   ├── preprocessing/          # Stage 2: Cleaning
│   │   ├── cleaner.py          # Arabic NLP (tashkeel removal)
│   │   └── pipeline.py         # Processing logic
│   ├── storage/                # Stage 3: Database
│   │   ├── db_manager.py       # Supabase/Postgres client
│   │   └── schema.sql          # SQL Schema (moved here)
│   ├── embeddings/             # Stage 4: Vectors
│   │   └── generator.py        # E5 model wrapper
│   ├── vectorstore/            # Stage 5: Qdrant
│   │   └── manager.py          # Qdrant client (CRUD + search)
│   ├── search/                 # Stage 6: Hybrid Search
│   │   └── engine.py           # RRF fusion engine
│   └── api/                    # Stage 7: Web API
│       ├── __init__.py
│       └── main.py             # FastAPI App
├── scripts/                    # THE MENU (Executables)
│   ├── run_full_pipeline.py
│   ├── scrape_all.py
│   ├── preprocess_data.py
│   ├── ingest_to_db.py
│   ├── generate_embeddings.py
│   ├── load_to_qdrant.py
│   ├── search.py               # ⭐ CLI Search Tool
│   ├── discover_poet.py
│   └── add_poet.py
├── configs/
│   └── poets.yaml
├── data/
│   ├── raw/poems_all.jsonl
│   ├── processed/poems_cleaned.jsonl
│   └── embeddings/poems_with_embeddings.jsonl
├── docs/
│   ├── README.md               # Knowledge base index
│   ├── project_flow.md         # ← YOU ARE HERE
│   ├── architecture/
│   ├── decisions/
│   ├── techniques/
│   └── troubleshooting/
├── .env                        # Secret keys (Qdrant, Supabase)
├── .gitignore
├── requirements.txt
└── diwanic_plan.md             # Original master plan
```

---

## ⭐ 5. How to Run

### One command pipeline:
```bash
./venv/bin/python scripts/run_full_pipeline.py --poems 30
```

### Search from CLI:
```bash
./venv/bin/python scripts/search.py "قصائد حزينة عن الفراق"
```

### Run Web API Server:
```bash
./venv/bin/python -m uvicorn diwanic.api.main:app --reload
```

---
## 🧠 V2.0 - New Technologies & Concepts You Will Learn

| # | Technology / Concept | Why for Diwanic | Difficulty |
|:--|:---------------------|:-----------------|:-----------|
| 1 | **`instructor`** (Library) | Forces an LLM to output JSON (e.g., `{"poet":"أبو نواس","mood":"حزين"}`) so our FastAPI can read it. | Medium |
| 2 | **Prompt Engineering** | Writing a prompt that tells the LLM: *"You are an Arabic poetry librarian. Extract poet, era, and theme from any query."* | Medium |
| 3 | **OpenAI / Groq API** | Calls to an external LLM to do the "thinking" for user intent. | Easy |
| 4 | **Langfuse Tracing** | A dashboard that tracks latency and cost of every call to the LLM and databases. | Medium |
| 5 | **Structured Output / Pydantic** | Defining a Python class like `class QueryIntent(BaseModel)` that tells the LLM exactly what fields to return. | Easy-Hard |
| 6 | **Cross-Encoder Re-ranker** | A second model that takes each search result and the query and gives a "true relevance" score. | Hard |
| 7 | **Guardrails** | Rules like: *"If no result scores > 0.5, say 'I don't know' instead of returning bad results."* | Easy |
| 8 | **Gradio / Telegram Bot** | A real chat interface. Instead of typing in Swagger UI, you text your bot from your phone. | Medium |
| 9 | **LangGraph (Agentic Loop)** | Code that can loop: *"Search → Check if results are good enough → If not, try a broader search → Return."* | Hard |

### 🏁 How we will start V2.0
When you return, we will:
1.  **Build the Router Agent** — A small LLM function that converts any user query into a structured search command.
2.  **Rewrite `engine.py`** — Add the routing layer on top of the existing search logic.
3.  **Test with Malay, English, and Mixed queries** — To see the multilingual power.

**No rush, take your time. The project is stable, the API is running, and the data is safe. Just say the word when you're ready!**
