# 📚 Diwanic — Arabic Poetry Retrieval System (Master Plan)

## 🧠 Vision

Diwanic is an Arabic poetry retrieval system that allows users to search classical and modern Arabic poetry using natural language queries.

It combines:
- Web scraping of Arabic poetry websites
- Structured data engineering
- Arabic NLP preprocessing
- Vector embeddings (semantic search)
- Keyword search (BM25)
- Hybrid ranking system
- Fast API serving layer

---

## 🧭 High-Level System Design

```
User Query
    ↓
Arabic Normalization
    ↓
Query Embedding
    ↓
Vector Search (Qdrant)   ←→   Keyword Search (BM25)
    ↓
Hybrid Score Fusion
    ↓
Optional Reranking
    ↓
Final Results
```

---

## 🏗️ Final Project Structure (Target)

```
diwanic/
│
├── src/
│   └── diwanic/
│       ├── core/
│       │   ├── logger.py
│       │   ├── config.py
│       │
│       ├── scraper/
│       │   ├── fetcher.py
│       │   ├── parser.py
│       │   ├── pipeline.py
│       │   ├── crawler.py
│       │   ├── models.py
│       │   └── utils.py
│       │
│       ├── preprocessing/
│       ├── embeddings/
│       ├── vectorstore/
│       ├── search/
│       └── api/
│
├── configs/
│   ├── scraper.yaml
│   ├── embedding.yaml
│   ├── retrieval.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── embeddings/
│
├── scripts/
│   ├── run_scraper.py
│   ├── ingest_data.py
│
├── tests/
├── requirements.txt
├── README.md
└── .env
```

---

## 🚀 Phase 1 — Scraper Foundation

### 🎯 Goal
Extract structured Arabic poetry data from websites like [Aldiwan.net](https://www.aldiwan.net).

### 🔧 Components

| Component | Responsibility |
|-----------|---------------|
| **Fetcher** | Downloads HTML pages, handles headers & requests |
| **Parser** | Extracts poem title, poet name, verses, metadata (era, meter, category) |
| **Pipeline** | Orchestrates scraping, handles errors & retries, adds delays |
| **Logger** | Tracks progress, logs errors & success rates (replaces `print`) |
| **Config (CDD)** | Controls scraper behavior via YAML |

### 📄 Scraper Config (CDD)

```yaml
base_url: "https://www.aldiwan.net"
delay: 1.5

headers:
  user_agent: "Mozilla/5.0 (DiwanicBot/1.0)"
```

### 📦 Output Data Structure

```json
{
  "title": "",
  "poet": "",
  "verses": [],
  "era": "",
  "meter": "",
  "category": "",
  "source_url": ""
}
```

### ✅ Phase 1 Deliverable

- 20–100 clean poems scraped
- Stored in `data/raw/`
- Verified structure consistency

---

## 🧹 Phase 2 — Crawler System

### 🎯 Goal
Automatically discover poem URLs.

### Features

- Pagination handling
- Category crawling
- Poet page crawling
- URL discovery engine

### ✅ Phase 2 Deliverable

- 1,000+ poem URLs discovered

---

## 🧼 Phase 3 — Arabic NLP Preprocessing

### 🎯 Goal
Clean Arabic text for retrieval quality.

### ⚠️ Important Note

> We follow the native Arabic approach — **preserve** Alef variants (أ إ آ) and Ta Marbuta (ة). Diacritics (tashkeel) are removed for search but the original text is kept for display.

### Steps

1. Keep original text as-is for display
2. Create a searchable variant:
   - Remove diacritics (tashkeel)
   - Remove noise/punctuation
   - **Keep all letter forms** (أ إ آ ة preserved)
3. Store both versions

### ✅ Phase 3 Deliverable

- Cleaned + standardized text ready for embedding

---

## 🧠 Phase 4 — Embedding System

### 🎯 Goal
Convert poetry into vector representations.

### Components

- Embedding model (multilingual or Arabic-specific)
- Batch embedding pipeline
- Storage of embeddings

### Embedding Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| Full poem | One vector per poem | General search |
| Verse-level | One vector per verse | Fine-grained similarity (optional) |

### ✅ Phase 4 Deliverable

- Embeddings generated and stored for all poems

---

## 🗄️ Vector Database — Qdrant

### Stored Data

- Embeddings (dense vectors)
- Metadata (poet, era, meter, category)
- Sparse vectors for BM25 (if using Qdrant's hybrid mode)

---

## 🔍 Phase 5 — Retrieval System

### 🎯 Goal
Implement hybrid search.

### 1. Semantic Search

- Vector similarity via Qdrant
- Understands meaning beyond keywords

### 2. Keyword Search (BM25)

- Exact word matching
- Poet names
- Rare Arabic words

### 3. Hybrid Fusion

```
final_score = 0.7 × semantic_score + 0.3 × keyword_score
```

Or using **Reciprocal Rank Fusion (RRF)**:

```
score = 1 / (60 + rank_vector) + 1 / (60 + rank_bm25)
```

---

## ⚡ Phase 6 — Reranking (Optional)

- Improves precision
- Reranks top 50 → top 10 results
- Uses scoring model or transformer reranker

---

## 🌐 Phase 7 — API Layer

### Framework: FastAPI

| Endpoint | Description |
|----------|-------------|
| `GET /search?q=...` | Hybrid search with filters |
| `GET /poem/{id}` | Get single poem details |
| `GET /poet/{name}` | Browse poet's works |
| `GET /similar/{poem_id}` | Find similar poems |

---

## 🧪 Phase 8 — Evaluation

### Test Queries

| Arabic Query | English Equivalent |
|---|---|
| "قصائد عن الحزن" | Poems about sadness |
| "شعر المتنبي" | Al-Mutanabbi's poetry |
| "قصائد عن الغربة" | Poems about exile |
| "أشعار أندلسية" | Andalusian poetry |

### Metrics

- Relevance (human-rated)
- Precision@k
- Recall@k
- Retrieval quality

---

## 🚀 Phase 9 — Deployment

| Stage | Tool |
|-------|------|
| Containerization | Docker |
| Hosting | VPS / Railway / Fly.io |
| API | FastAPI + Uvicorn |
| Database | Qdrant Cloud + PostgreSQL |

---

## ⚙️ Design Principles

- **Keep scraper modular** — separate fetch / parse / pipeline
- **Use config-driven development (CDD)** — YAML over hardcoded values
- **Avoid premature optimization** — start simple, scale later
- **Log everything** — logger replaces print statements
- **Data quality first** — bad scraping = bad retrieval = bad embeddings

---

## 🧠 Important Rule

> Data quality matters more than model choice.

If scraping is bad → retrieval is bad → embeddings won't help.

---

## 📌 First Milestone (Start Here)

1. Scrape **1 poem**
2. Parse structure correctly
3. Expand to **20 poems**
4. Save in JSON
5. Validate consistency

**Only then** move forward.

---

## 🧭 Final Goal

A system where users can search:

- "poems about exile"
- "sad Abbasid poetry"
- "poems similar to Al-Mutanabbi"

and receive:

- ✅ Semantically relevant poems
- ✅ Accurate metadata filtering
- ✅ Fast retrieval results

---

## 🗺️ Quick Reference — All Phases

| Phase | Name | Deliverable |
|-------|------|-------------|
| 1 | Scraper Foundation | 20–100 poems in `data/raw/` |
| 2 | Crawler System | 1,000+ discovered URLs |
| 3 | Arabic NLP Preprocessing | Cleaned, normalized text |
| 4 | Embedding System | Vectors for all poems |
| 5 | Retrieval System | Hybrid search working |
| 6 | Reranking | Improved precision |
| 7 | API Layer | FastAPI endpoints live |
| 8 | Evaluation | Metrics & test queries |
| 9 | Deployment | Docker + cloud hosting |

---

## 🚦 How to Start

Say:

> **"Let's start Phase 1"**

And we will:

1. Set up the Python virtual environment
2. Install dependencies (`requests`, `beautifulsoup4`, `pyyaml`)
3. Build the `fetcher.py` — download a page from Aldiwan.net
4. Build the `parser.py` — extract poem data from the HTML
5. Test with 1 poem, then scale to 20
