<p align="center">
  <img src="docs\assets\logo.png" width="700">
</p>

# Diwanic: Semantic Search for Arabic Poetry

**Diwanic** is a production-grade Retrieval-Augmented Generation (RAG) system designed to enable semantic search across Arabic poetry collections. Rather than matching exact keywords, Diwanic uses multilingual embeddings and hybrid retrieval strategies to surface verses based on semantic meaning, emotional resonance, and thematic coherence. The system combines vector similarity search with full-text retrieval, intelligent query routing, and LLM-powered contextualization to deliver precise, interpretable results. It demonstrates how to build scalable semantic search systems for low-resource languages and serves as a reference implementation for RAG architectures on multilingual corpora.

---

## Problem Statement

### Why Keyword Search Falls Short

Traditional information retrieval systems rely on exact or fuzzy keyword matching. For Arabic poetry, this approach encounters fundamental limitations:

1. **Morphological Richness**: Arabic words inflect dramatically (e.g., فرح "joy" becomes مفرحة "delightful"). Keyword search misses related forms.

2. **Poetic Abstraction**: Verses often express concepts indirectly through metaphor and imagery. A search for "longing" (`حنين`) might miss verses using "absence" (`الفراق`) or "remembrance" (`الذكر`).

3. **Semantic Ambiguity**: Arabic is highly context-dependent. The same word carries different meanings across eras, dialects, and poetic traditions.

4. **Structural Discontinuity**: Poetry is often organized by verse (بيت), not by semantic units. A single "meaningful chunk" may span multiple verses or lie fragmented across lines.

### Why Semantic Retrieval is Necessary

Semantic search overcomes these limitations by:

- **Representing meaning as vectors**: Embedding models encode entire phrases into a shared semantic space, capturing relationships between concepts rather than surface forms.
- **Enabling cross-morphological search**: Vectors capture underlying semantics, so different word forms expressing the same idea cluster together.
- **Supporting thematic exploration**: Users can search for feelings, concepts, and philosophical ideas rather than exact terms.

### Challenges in Arabic Poetry Search

1. **Limited Embedding Models**: Few high-quality Arabic embedding models exist. General multilingual models often perform poorly on poetry due to domain shift.

2. **Sparse Data**: Historical poetry collections are smaller than modern corpora, making fine-tuned embeddings difficult.

3. **Meter and Structure**: Classical Arabic poetry follows strict metrical rules (بحور الشعر). Understanding meaning often requires awareness of prosodic structure—something embedding models typically ignore.

4. **Dialectal Variation**: Poetry spans centuries and regions. Classical, pre-Islamic, and modern poetry use different dialects and vocabulary.

---

## System Architecture

### High-Level Design

Diwanic orchestrates three core components working in concert:

```mermaid
graph LR
    A["User Query\n(Natural Language)"]
    B["Intent Router\n(Query Planning)"]
    C["Embedding Model\n(Semantic Encoding)"]
    D["Hybrid Retriever\n(Vector + Keyword)"]
    E["Database\n(Qdrant + PostgreSQL)"]
    F["Context Assembler\n(Result Ranking)"]
    G["Response"]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> D
    D --> F
    F --> G
```

### Component Responsibilities

#### 1. **Intent Router** (`diwanic/search/router.py`)
**Purpose**: Translate natural-language queries into structured retrieval plans.

Receives a raw user query in Arabic and produces a `SearchPlan` containing:
- `semantic_query`: A normalized representation of the user's intent in Classical Arabic
- `filters`: Structured metadata filters (poet name, era, thematic category)
- `intent_type`: One of `search_poems` or `ask_about_poet`

**Implementation**: Uses an LLM (via 9Router/OpenAI-compatible endpoint) to perform deterministic extraction. Rather than treating the LLM as a black box, we prompt it to output JSON with strict schema validation.

**Why This Design**:
- Stateless and deterministic (same query always produces the same plan)
- Decouples query understanding from retrieval logic
- Enables debugging of retrieval failures by inspecting the plan

---

#### 2. **Embedding Model** (SentenceTransformers)
**Purpose**: Convert text into fixed-size vectors that capture semantic meaning.

Uses `intfloat/multilingual-e5-small`:
- Trained on 50+ languages including Modern Standard Arabic
- 384-dimensional embeddings
- Efficient (~134M parameters) for production deployment
- Supports both queries and documents

**Why This Model**:
- Trained on multilingual corpora, understands Arabic
- Efficient for real-time inference
- Competitive with larger models on retrieval benchmarks
- Small enough for CPU deployment if needed

---

#### 3. **Hybrid Retriever** (`diwanic/search/engine.py`)
**Purpose**: Execute a two-stage retrieval pipeline combining vector and keyword search.

**Stage 1: Vector Search (Qdrant)**
- Embeds the user query using SentenceTransformers
- Executes approximate nearest neighbor search in the `poems` collection
- Returns top-K verses by cosine similarity

**Stage 2: Keyword Search (PostgreSQL)**
- Parses the user query for semantically important Arabic terms
- Executes full-text search in PostgreSQL using GIN indexes
- Scores documents by term frequency and term importance

**Stage 3: Reciprocal Rank Fusion (RRF)**
- Combines rankings from both retrieval stages
- Formula: `score = 1 / (k + rank)` where k=60 (a tuning parameter)
- Ensures diversity: high recall from keyword search + precision from vectors

**Stage 4: Postgres Hydration ("Postgres-as-Truth")**
- Constructs authoritative result objects by querying PostgreSQL metadata
- Every result is enriched with poet name, era, category, full poem text, etc.
- Single source of truth for data consistency

---

#### 4. **Vector Database** (Qdrant)
**Purpose**: Store and index poem embeddings for efficient similarity search.

**Design**:
- Collection name: `poems`
- Payload schema: `poem_id`, `verse_index`, `text_vector` (384 dimensions)
- Index type: HNSW (Hierarchical Navigable Small World) for approximate search
- Distance metric: Cosine similarity

**Why Qdrant**:
- Production-grade vector database with horizontal scaling
- HNSW algorithm balances latency and accuracy
- Built-in filtering on metadata (e.g., "filter by era")
- Supports incremental updates and versioning

---

#### 5. **SQL Database** (PostgreSQL)
**Purpose**: Store authoritative metadata, support full-text search, maintain data lineage.

**Schema**:
```
Poets Table:
  id (serial primary key)
  name (text, indexed)
  era (text, indexed)
  bio (text)

Poems Table:
  id (serial primary key)
  poet_id (foreign key)
  title (text)
  category (text)
  meter (text)
  verses (jsonb array)

SearchLog Table:
  id (serial primary key)
  query (text)
  results_count (int)
  latency_ms (int)
  timestamp (timestamp)
```

**Full-Text Search**: Uses PostgreSQL's built-in tsvector/tsquery for Arabic terms.

---

## High-Level Retrieval Flow

```mermaid
sequenceDiagram
    participant User
    participant Router as Intent Router
    participant Embedding as Embedding Model
    participant Retriever as Hybrid Retriever
    participant Qdrant as Vector DB
    participant Postgres as PostgreSQL
    participant Ranker as RRF Ranker
    
    User->>Router: Raw Query
    Router->>Embedding: Semantic Plan
    Embedding->>Retriever: Embedding Vector
    Retriever->>Qdrant: Vector Search (Top-20)
    Qdrant-->>Retriever: Ranked Verses
    Retriever->>Postgres: Full-Text Search
    Postgres-->>Retriever: Full-Text Results
    Retriever->>Ranker: Two Rankings
    Ranker->>Postgres: Fetch Metadata
    Postgres-->>Ranker: Enriched Results
    Ranker-->>User: Final Ranked Results
```

### Stage Breakdown

| Stage | Responsibility | Latency | Input | Output |
|-------|-----------------|---------|-------|--------|
| Intent Routing | Parse and structure user intent | 200-400ms | Raw query | SearchPlan |
| Embedding | Vectorize semantic query | 10-20ms | Semantic query | 384-dim vector |
| Vector Search | Find similar verses in Qdrant | 20-50ms | Query vector | Top-20 verses with scores |
| Keyword Search | Full-text match in PostgreSQL | 30-100ms | Query terms | Matching verses with scores |
| RRF Fusion | Combine both rankings | 5-10ms | Two ranked lists | Unified ranking |
| Hydration | Enrich with metadata | 50-150ms | Verse IDs | Complete SearchResult objects |
| **Total** | **End-to-end latency** | **315-730ms** | User query | Ranked, contextualized results |

---

## Repository Structure

```
diwanic/
│
├── diwanic/                         # Main package
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── ui.py                    # Gradio web interface (discovery UI)
│   │   ├── database.py              # SQLAlchemy session factory
│   │   └── routes/
│   │       └── search_routes.py      # REST API endpoints (/search, /poem)
│   │
│   ├── search/
│   │   ├── engine.py                # HybridSearchEngineV2 (2-stage retrieval)
│   │   ├── router.py                # IntentRouter (query planning)
│   │   ├── evaluation.py            # Retrieval metrics (NDCG, MRR)
│   │   ├── rrf.py                   # Reciprocal rank fusion implementation
│   │   └── api_models.py            # Pydantic schemas for API
│   │
│   ├── schemas/
│   │   ├── query.py                 # SearchPlan, QueryFilter dataclasses
│   │   └── search.py                # SearchResult dataclass
│   │
│   ├── embeddings/
│   │   └── generator.py             # SentenceTransformer wrapper
│   │
│   ├── vectorstore/
│   │   ├── manager.py               # VectorStoreManager (Qdrant lifecycle)
│   │   └── verse_store.py           # Verse-level embedding operations
│   │
│   ├── storage/
│   │   └── repository.py            # PostgreSQL Repository pattern
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py               # Arabic text normalization
│   │   ├── pipeline.py              # Multi-stage preprocessing
│   │   └── text_utils.py            # Tokenization, segmentation
│   │
│   ├── scraper/
│   │   ├── fetcher.py               # HTTP client for poetry sources
│   │   ├── parser.py                # HTML parsing logic
│   │   └── models.py                # Poem schema
│   │
│   ├── pipelines/
│   │   ├── flows/
│   │   │   └── full_pipeline_flow.py # Prefect orchestration
│   │   └── tasks/
│   │       ├── scrape_task.py        # Data ingestion task
│   │       ├── preprocess_task.py    # Cleaning task
│   │       ├── embed_task.py         # Embedding task
│   │       └── ingest_task.py        # Vector DB load task
│   │
│   ├── core/
│   │   ├── config.py                # Configuration management (Pydantic)
│   │   └── observability.py         # Logfire setup
│   │
│   ├── utils/
│   │   ├── logger_util.py           # Logging setup
│   │   ├── text_splitter.py         # Semantic chunking
│   │   └── text_utils.py            # Utility functions
│   │
│   ├── infrastructure/
│   │   └── qdrant.py                # Qdrant client factory
│   │
│   ├── discovery.py                 # Auto-discovery utilities
│   ├── __init__.py
│
├── data/
│   ├── raw/                         # Original, unprocessed poems
│   │   ├── poems_all.jsonl
│   │   └── poems_expanded.jsonl
│   ├── processed/                   # Cleaned, normalized poems
│   │   ├── poems_cleaned.jsonl
│   │   └── poems_expanded_cleaned.jsonl
│   └── embeddings/                  # Pre-computed embeddings
│       └── poems_with_embeddings.jsonl
│
├── configs/
│   └── poets.yaml                   # Poet metadata configuration
│
├── docs/
│   ├── architecture/
│   │   └── 01-data-flow.md          # Data flow documentation
│   ├── decisions/
│   │   ├── 01-schema-design.md      # Database schema rationale
│   │   ├── 02-arabic-normalization.md
│   │   └── 03-flat-structure.md
│   ├── techniques/
│   │   └── 04-arabic-cleaning.md
│   └── troubleshooting/
│       └── 01-module-not-found.md
│
├── scripts/
│   ├── set_github_secrets.py        # GitHub Actions setup
│   └── migration_scripts/           # Database migration utilities
│
├── notebook/
│   └── scrapper_exploration.ipynb   # Exploratory data analysis
│
├── tests/
│   ├── test_initialization.py       # Unit tests
│   └── golden_set.jsonl             # Test fixtures
│
├── pyproject.toml                   # Python packaging config
├── Makefile                         # Development commands
├── docker-compose.yml               # Local stack (Qdrant + Postgres)
├── Dockerfile                       # Container image
│
└── README.md                        # This file
```

---

## Technology Stack

| Component | Technology | Purpose | Why This Choice |
|-----------|-----------|---------|-----------------|
| **Language** | Python 3.9+ | Core implementation | Rich ML ecosystem, strong type hints |
| **Web Framework** | FastAPI | REST API | Async-native, automatic OpenAPI docs, high performance |
| **Web UI** | Gradio | Interactive interface | Minimal boilerplate for ML demos, built-in RTL support |
| **Embedding Model** | SentenceTransformers | Semantic encoding | Multilingual, efficient, competitive performance |
| **Vector Database** | Qdrant | Vector storage & search | Production-ready, HNSW indexing, metadata filtering |
| **SQL Database** | PostgreSQL | Metadata & full-text search | Robust, GIN indexes for Arabic, ACID compliance |
| **Task Orchestration** | Prefect | ETL pipelines | Declarative DAG, dynamic scheduling, observability |
| **Configuration** | Pydantic | Settings management | Type-safe, environment validation, structured defaults |
| **Observability** | Logfire | Monitoring & tracing | Structured logging, LLM observability, OpenTelemetry |
| **ORM** | SQLAlchemy | Database abstraction | Async support, migration-friendly, type-aware queries |
| **Testing** | Pytest | Unit & integration tests | Fixtures, parametrization, clear assertions |
| **Deployment** | Docker Compose | Local development | Reproducible environments, service isolation |
| **API Client** | OpenAI (9Router) | Intent routing | Standard interface, provider-agnostic |

---

## Design Decisions

### 1. Why Hybrid Search (Vector + Keyword)?

**Decision**: Implement two-stage retrieval combining embeddings and full-text search, fused via RRF.

**Rationale**:
- **Vector search alone** excels at semantic similarity but misses exact-match queries (e.g., searching for a specific poet's name).
- **Keyword search alone** requires exact term matches, limiting discovery of thematic variants.
- **Hybrid approach** balances **precision** (keywords) with **recall** (embeddings).

**Tradeoff**: Higher latency (~300-700ms) vs. simpler single-stage retrieval (~50-150ms), but justified by superior result quality.

---

### 2. Why Reciprocal Rank Fusion (RRF)?

**Decision**: Combine vector and keyword rankings using RRF instead of weighted averaging.

**Rationale**:
- RRF is **rank-agnostic**: treats positions rather than raw scores, eliminating scale mismatch between Qdrant similarity and PostgreSQL match weights.
- **Robust**: doesn't require tuning blend weights (unlike `0.6 * vector_score + 0.4 * keyword_score`).
- **Proven**: used by leading search systems (Elasticsearch, Solr).

**Formula**: `score(d) = Σ (1 / (k + rank(d)))`  where k=60 (tuning constant).

---

### 3. Why PostgreSQL as "Source of Truth"?

**Decision**: Store definitive metadata in PostgreSQL; Qdrant holds only embeddings and verse indices.

**Rationale**:
- **Consistency**: Single authoritative version of poems, poets, and relationships.
- **Auditability**: PostgreSQL transaction logs provide lineage.
- **Flexibility**: Easy to update poet metadata or fix verses without re-embedding.
- **ACID**: Ensures no orphaned embeddings or corrupted state.

**Architectural Principle** ("Postgres-as-Truth"):
```
Retrieval Result = Vector DB lookup + Postgres hydration
SearchResult(
    poem_id = verse["poem_id"],  # From Qdrant
    text = postgres.fetch(poem_id).text,  # From Postgres
    poet = postgres.fetch(poem_id).poet,  # From Postgres
    score = rrf_score,
)
```

---

### 4. Why SentenceTransformers Over Fine-Tuned Models?

**Decision**: Use pre-trained `intfloat/multilingual-e5-small` rather than fine-tune on domain-specific Arabic poetry.

**Rationale**:
- **Data scarcity**: Arabic poetry collection is ~1,000 poems—too small for stable fine-tuning.
- **Transfer learning**: Pre-trained models learn general semantic relationships; poetry-specific patterns can emerge without explicit fine-tuning.
- **Deployment simplicity**: Reduces model complexity and inference cost.
- **Reproducibility**: Standard, published model ensures others can replicate results.

**Future Path**: Once collection reaches ~10,000 poems with labeled relevance pairs, consider fine-tuning on poetry-specific objectives.

---

### 5. Why Prefect for Pipelines?

**Decision**: Use Prefect for ETL orchestration rather than Airflow or simple scripts.

**Rationale**:
- **Dynamic DAGs**: Pipeline structure can depend on runtime data (e.g., process only new poems since last run).
- **Observable**: Built-in tracing and retry logic.
- **Pythonic**: Define flows as Python code, not YAML configs.

**Pipeline Stages**:
```
scrape_task() → preprocess_task() → embed_task() → ingest_task()
```

---

### 6. Why Verse-Level Embeddings?

**Decision**: Embed individual verses (بيت) rather than entire poems.

**Rationale**:
- **Granularity**: Users can match on specific lines with thematic resonance.
- **Recall**: More vectors = higher chance of retrieving relevant content.
- **Semantic coherence**: Each verse is a self-contained thought in classical poetry.

**Tradeoff**: Larger vector DB (more storage, more to index) vs. improved search precision.

---

## Example Query Flow

### Scenario: User searches for "Poems about longing and separation"

**Step 1: Intent Routing**
```
Input: "قصائد عن الحنين والفراق"
         (Poems about longing and separation)

Router output (SearchPlan):
{
  "semantic_query": "الحنين والفراق والشوق",
  "filters": {},
  "intent": "search_poems"
}
```

**Step 2: Embedding**
```
Model embeds semantic_query → 384-dimensional vector
Vector ≈ [0.12, -0.45, 0.78, ..., 0.33]
```

**Step 3: Vector Search (Qdrant)**
```
Query: Top-20 verses by cosine similarity
Results (by similarity):
  1. Verse from Al-Mutanabbi (score: 0.89)
  2. Verse from Imru' al-Qais (score: 0.87)
  3. Verse from Dhu al-Rumma (score: 0.84)
  ...
```

**Step 4: Keyword Search (PostgreSQL)**
```
Arabic terms: حنين, فراق, شوق
Full-text query: tsquery_arabic('حنين | فراق | شوق')
Results (by TF-IDF):
  1. Poem by Al-Shafi'i (contains all 3 terms)
  2. Poem by Antara (contains 2 terms)
  3. Poem by Al-Niffari (contains 1 term)
  ...
```

**Step 5: RRF Fusion**
```
Combine rankings:
  Final Score = 1/(60 + vector_rank) + 1/(60 + keyword_rank)
  
Fused ranking:
  1. Al-Mutanabbi verse (high in both)
  2. Al-Shafi'i poem (strong keyword match)
  3. Imru' al-Qais verse (strong vector match)
  ...
```

**Step 6: Postgres Hydration**
```
For each result, fetch metadata:
  SearchResult(
    poem_id=5,
    verse_index=3,
    text="وما الحب إلا في الفراق جمال",
    poet="المتنبي",
    era="عصر عباسي",
    category="الحنين",
    score=0.78
  )
```

**Final Output to User**:
```json
{
  "query": "قصائد عن الحنين والفراق",
  "results_count": 12,
  "results": [
    {
      "poem_id": 5,
      "verse": "وما الحب إلا في الفراق جمال",
      "poet": "المتنبي",
      "era": "العصر العباسي",
      "relevance_score": 78,
      "explanation": "Verse directly addresses longing within separation"
    },
    ...
  ],
  "latency_ms": 425
}
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ (or use Docker)
- Qdrant (vector database)
- pip or Poetry

### Quick Start

**1. Clone the repository**:
```bash
git clone https://github.com/your-org/diwanic.git
cd diwanic
```

**2. Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**:
```bash
pip install -e ".[dev]"
```

**4. Configure environment** (interactive setup):
```bash
python setup_env.py
```

This wizard will prompt you for:
- PostgreSQL connection URL
- Qdrant vector database URL
- LLM router API credentials
- Model name for query planning

Alternatively, create `.env` manually:
```bash
cp .env.example .env
# Edit .env with your configuration
```

**5. Start services** (using Docker Compose):
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Qdrant (port 6333)

**6. Initialize database**:
```bash
python -m diwanic.app.database  # Create tables
```

**7. Ingest sample data**:
```bash
make run-flow  # Run Prefect pipeline
```

**8. Launch UI**:
```bash
python -m diwanic.app.ui
```

Open browser to `http://localhost:7860`

---

## Environment Variables

Create `.env` in project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/diwanic
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/diwanic

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-api-key

# LLM / Intent Router (via 9Router)
ROUTER_BASE_URL=https://api.9router.com/v1
ROUTER_API_KEY=your-api-key-here
ROUTER_MODEL=gpt-4-turbo

# Embedding Model (HuggingFace)
EMBEDDING_MODEL=intfloat/multilingual-e5-small

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development

# Observability
LOGFIRE_TOKEN=your-logfire-token
```

### Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | N/A | PostgreSQL connection string (required) |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant service URL |
| `QDRANT_API_KEY` | None | Qdrant API key (if remote) |
| `ROUTER_BASE_URL` | N/A | LLM router endpoint |
| `ROUTER_API_KEY` | N/A | LLM router auth token |
| `ROUTER_MODEL` | `gpt-4-turbo` | LLM model for query routing |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-small` | SentenceTransformer model |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## How to Run

### Run the Web UI (Gradio)
```bash
python -m diwanic.app.ui
```
Launches at `http://localhost:7860`

Features:
- Beautiful discovery interface with hero banner
- Era and poet carousels
- Responsive poem cards with mood tags
- Full-featured search
- Poem detail panel

---

### Run the REST API (FastAPI)
```bash
python -m diwanic.app.main
```
Launches at `http://localhost:8000`

**Endpoints**:

```bash
# Search poems by meaning
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "قصائد عن الحنين",
    "limit": 10
  }'

# Get poem details
curl "http://localhost:8000/poem/5"

# Health check
curl "http://localhost:8000/health"
```

### Run the Ingestion Pipeline
```bash
make run-flow
```

Stages:
1. **Scrape**: Download poems from configured sources
2. **Preprocess**: Normalize Arabic text, tokenize, clean
3. **Embed**: Generate embeddings for each verse
4. **Ingest**: Load vectors into Qdrant, metadata into PostgreSQL

---

### Run Tests
```bash
pytest tests/ -v
```

---

## Example Usage

### Python Client

```python
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter

# Initialize
router = IntentRouter()
engine = HybridSearchEngineV2()

# Analyze query
query = "قصائد عن الحب والفراق"
plan = router.analyze_query(query)
print(f"Semantic query: {plan.semantic_query}")

# Execute search
results = engine.search(plan, limit=10)

# Display results
for result in results:
    print(f"\n{result.poet} - {result.era}")
    print(f"Score: {result.score:.2%}")
    print(result.original_text)
```

### REST API Examples

**Example 1: Search for poems about patience**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "قصائد عن الصبر والتحمل",
    "limit": 5
  }'
```

**Response**:
```json
{
  "query": "قصائد عن الصبر والتحمل",
  "results_count": 5,
  "results": [
    {
      "poem_id": 12,
      "verse_text": "والصبر عند المصائب يجلب الفرج",
      "poet": "الشافعي",
      "era": "عصر عباسي",
      "relevance_score": 0.87
    }
  ]
}
```

**Example 2: Filter by poet**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "الحب والغزل",
    "filters": {
      "poet_name": "المتنبي"
    },
    "limit": 3
  }'
```

**Example 3: Cross-era search**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "الشجاعة والفروسية",
    "limit": 10
  }'
```

---

## What You Can Learn From This Repository

This codebase demonstrates production-grade patterns for:

### 1. **Retrieval-Augmented Generation (RAG)**
- Hybrid retrieval combining multiple signals
- Ranking fusion strategies (RRF, weighted combinations)
- Query routing and intent detection

### 2. **Embeddings & Vector Databases**
- Using multilingual embeddings for semantic search
- HNSW indexing and approximate nearest neighbor search
- Metadata filtering in vector DBs
- Embedding model selection tradeoffs

### 3. **Low-Resource Language NLP**
- Handling morphologically rich languages
- Preprocessing and normalization for Arabic
- Leveraging pre-trained multilingual models
- Limited data scenarios

### 4. **Search System Architecture**
- Full-text search with PostgreSQL
- Vector similarity search with Qdrant
- Combining multiple retrieval signals
- Result ranking and scoring

### 5. **Python Best Practices**
- Type hints and Pydantic validation
- Async/sync patterns in FastAPI
- Repository pattern for data access
- Configuration management
- Structured logging and observability

### 6. **Production Systems**
- Error handling and fallbacks
- Health checks and monitoring
- Database connection pooling
- API design and versioning
- Docker containerization

---
<!-- 
## Future Roadmap

### Phase 1: Enhanced Retrieval (Q2 2024)
- [ ] **Dense passage retrieval (DPR)**: Train poem-specific encoder on collected relevance pairs
- [ ] **Hybrid reranking**: Use a cross-encoder to re-rank fusion results
- [ ] **Query expansion**: Automatically expand queries with synonyms and related concepts
- [ ] **Semantic caching**: Cache query embeddings and results for repeat queries

### Phase 2: Understanding Poetic Structure (Q3 2024)
- [ ] **Meter classification**: Detect and filter by poetic meter (بحور)
- [ ] **Rhyme analysis**: Extract and match on rhyme scheme
- [ ] **Structural parsing**: Segment poems into semantic units beyond verse boundaries
- [ ] **Figure-of-speech detection**: Tag metaphors, similes, personification

### Phase 3: Knowledge Graphs (Q4 2024)
- [ ] **Poet relationship network**: Extract and visualize poet influences
- [ ] **Thematic graph**: Build semantic network of poetry themes
- [ ] **GraphRAG**: Use knowledge graph for context-aware retrieval
- [ ] **Historical timeline**: Map poems on era and influence timeline

### Phase 4: Multimodal & Advanced Features (2025)
- [ ] **Audio integration**: Embed recitations with text
- [ ] **Annotation system**: Community-driven poem annotations and translations
- [ ] **Fine-tuned embeddings**: Collect relevance feedback, train domain model
- [ ] **Multi-agent system**: Specialist agents for different poetry aspects
- [ ] **Explanation generation**: Detailed LLM explanations for why verses matched

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Install dev dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Write tests** for your changes:
   ```bash
   pytest tests/ -v
   ```

4. **Follow code style** (checked by Ruff):
   ```bash
   ruff check diwanic/
   ruff format diwanic/
   ```

5. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push and create a Pull Request** with:
   - Detailed description of changes
   - Link to related issues
   - Test results
   - Updated documentation

-->

## License

Diwanic is released under the MIT License. See [LICENSE](LICENSE) file for details.

---

## Citation

If you use Diwanic in your research or project, please cite:

```bibtex
@software{diwanic2024,
  title = {Diwanic: Semantic Search for Arabic Poetry},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/your-org/diwanic}
}
```

---

## Support

For questions, issues, or discussions:

- **Issues**: [GitHub Issues](https://github.com/your-org/diwanic/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/diwanic/discussions)
- **Email**: [contact@example.com](mailto:amarpoji1999@example.com)

---

**Built with ❤️ for the exploration and preservation of Arabic poetry.**
```
