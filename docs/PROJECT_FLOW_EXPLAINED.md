# Diwanic: How It Works (Explained Like You're 5)

**What is Diwanic?** A search engine for Arabic poetry. You type a question in Arabic (like "أبيات عن الحب" — verses about love), and Diwanic finds the most beautiful matching poems.

---

## The Big Picture: 4 Steps

```
┌──────────────────────────────────────────────────────────┐
│  STEP 1          STEP 2          STEP 3         STEP 4   │
│  📥 SCRAPE   →   🧹 CLEAN   →   🧠 EMBED   →   💾 STORE │
│                                                          │
│  Get poems        Strip         Turn text      Put poems │
│  from website    diacritics    into numbers   in DBs    │
└──────────────────────────────────────────────────────────┘

    Then at search time:
    ┌──────────────────────────────────────────────────┐
    │  🔍 SEARCH → Find best poems using numbers + words │
    └──────────────────────────────────────────────────┘
```

---

## Step 1: Scrape — Grab Poems from the Internet

**File:** `diwanic/scraper/pipeline.py`  
**Helpers:** `fetcher.py`, `parser.py`, `models.py`

```
Aldiwan.net  →  scraper  →  data/raw/poems_all.jsonl
(website)         ↑          (file full of poems)
              Uses configs/poets.yaml
              (list of poets to scrape)
```

The scraper visits [aldiwan.net](https://aldiwan.net) and copies poems. It reads the HTML, finds the poem title, the poet's name, and every verse. Every poem becomes one line in a JSONL file.

**Output:** `data/raw/poems_all.jsonl` (one poem per line, raw messy text)

---

## Step 2: Clean — Make the Text Searchable

**File:** `diwanic/preprocessing/pipeline.py`  
**Helpers:** `cleaner.py`

Arabic text has small marks (tashkeel / تشكيل) above/below letters — like the fatHa (َ) and Damma (ُ). These marks are pretty but make searching hard because the same word can be written 10 different ways with them. We strip them.

Also we normalize alef variants (أ إ آ → ا) so they're all treated as the same letter.

**Input:** `data/raw/poems_all.jsonl`  
**Output:** `data/processed/poems_cleaned.jsonl` (clean text, same poems)

---

## Step 3: Embed — Turn Text into Numbers

**File:** `diwanic/embeddings/generator.py`

Computers can't "understand" Arabic text directly. We use a machine-learning model called `multilingual-e5-small` (from HuggingFace) that converts every poem into a list of 384 numbers. Poems with similar *meaning* get similar numbers.

```
"أبيات عن الشوق والحنين"  →  [0.12, -0.44, 0.88, ... 384 numbers]
"يا طيب暗恋 لا تسل"           →  [0.15, -0.40, 0.85, ... 384 numbers]  ← close!
```

**Input:** `data/processed/poems_cleaned.jsonl`  
**Output:** `data/embeddings/poems_with_embeddings.jsonl` (poems + their 384 numbers)

---

## Step 4: Store — Put Everything in Two Databases

### 4a. Postgres (the Brain) — structured data
**File:** `diwanic/storage/repository.py`

Postgres stores the facts: which poet wrote which poem, how many verses, the full text, metadata. This is the "source of truth."

Schema: poets → poems → verses (3 tables linked by IDs)

### 4b. Qdrant (the Nose) — vector search
**File:** `diwanic/vectorstore/manager.py` + `verse_store.py`

Qdrant stores the 384-number vectors. It's optimized for one thing: given a query vector, find the most similar vectors really fast. This is what makes semantic search work.

---

## Searching: How It Works When You Ask a Question

```
You: "أبيات عن جمال الطبيعة" (verses about the beauty of nature)
        ↓
    ┌─────────────────────────────┐
    │  1. ROUTER (router.py)       │  ← Understands what you mean
    │     "Natural language query" │
    │     → Structured SearchPlan   │
    └─────────────────────────────┘
        ↓
    ┌─────────────────────────────┐
    │  2. HYBRID SEARCH (engine.py) │  ← Does the actual looking
    │     Two searches run in parallel:
    │     (A) Vector search  → finds poems with similar MEANING
    │     (B) Keyword search  → finds poems with matching WORDS
    │     Both results combined using RRF
    └─────────────────────────────┘
        ↓
    ┌─────────────────────────────┐
    │  3. RRF (rrf.py)              │  ← Reciprocal Rank Fusion
    │     Merges rankings: if a poem │
    │     appears in both searches, │
    │     it gets boosted to top    │
    └─────────────────────────────┘
        ↓
    You: get ranked list of poems + verses
```

**RRF (Reciprocal Rank Fusion):** Think of it like a music chart that combines radio play AND streaming — poems that show up in both vector AND keyword search get a higher score than either alone.

---

## Who Runs Everything?

| Who | File | What it does |
|-----|------|-------------|
| **CLI** | `diwanic/cli/main.py` | You type commands in terminal |
| **API** | `diwanic/app/main.py` | Other apps can call Diwanic over HTTP |
| **Pipeline** | `diwanic/pipelines/flows/full_pipeline_flow.py` | Orchestrates all 4 steps in order |
| **Tasks** | `diwanic/pipelines/tasks/*.py` | Individual steps: scrape, clean, embed, ingest |

---

## How to Run

```bash
# 1. Run the full pipeline (Steps 1-4 all at once)
python -m diwanic.cli run-pipeline

# 2. Start the API server
python -m diwanic.cli serve

# 3. Search from command line
python -m diwanic.cli search "الحب والجمال"

# 4. Or search via HTTP
curl "http://localhost:8000/api/v2/search?q=الحب+والجمال"
```

---

## File Map: What Each File Does

| File | Role |
|------|------|
| `scraper/pipeline.py` | Orchestrates scraping all poets |
| `scraper/fetcher.py` | Makes HTTP requests to Aldiwan.net |
| `scraper/parser.py` | Reads HTML, extracts verses |
| `scraper/models.py` | Defines what a Poem looks like (dataclass) |
| `preprocessing/pipeline.py` | Orchestrates cleaning |
| `preprocessing/cleaner.py` | Strips tashkeel, normalizes Arabic |
| `embeddings/generator.py` | Converts poems to 384-dim vectors |
| `storage/repository.py` | All Postgres reads/writes |
| `vectorstore/manager.py` | Qdrant collection management |
| `vectorstore/verse_store.py` | Verse-level vector storage |
| `search/router.py` | Converts your query to a search plan |
| `search/engine.py` | Runs hybrid search + RRF |
| `search/rrf.py` | RRF scoring logic |
| `pipelines/flows/full_pipeline_flow.py` | Tie all steps together |
| `pipelines/tasks/*.py` | Individual Prefect tasks |
| `app/main.py` | FastAPI server setup |
| `api/routes/search_routes.py` | HTTP endpoint definitions |
| `cli/main.py` | Terminal commands |
| `core/config.py` | Reads .env, settings for everything |