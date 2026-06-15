# Diwanic Project Flow

## Overview

This document outlines the data flow and architecture of the Diwanic Arabic Poetry Retrieval System (V2). The system is designed to scrape, preprocess, embed, store, and search Arabic poetry from Aldiwan.net.

## Data Flow

```mermaid
flowchart LR
    A[Scraper] --> B[Preprocessing]
    B --> C[Embeddings]
    C --> D[Storage: Postgres + Qdrant]
    D --> E[Search Engine]
    E --> F[API/CLI]
```

### Stage 1: Scraping (`diwanic.scraper`)
- **Input**: Poet slugs from `configs/poets.yaml`
- **Process**: Fetch poem pages from Aldiwan.net, parse HTML, extract poem metadata and verses.
- **Output**: Raw JSONL files (`data/raw/poems_all.jsonl`)

### Stage 2: Preprocessing (`diwanic.preprocessing`)
- **Input**: Raw JSONL
- **Process**: 
  - Clean Arabic text (remove diacritics, normalize alef/hamza variants)
  - Generate searchable versions of text and metadata
- **Output**: Cleaned JSONL (`data/processed/poems_cleaned.jsonl`)

### Stage 3: Embedding Generation (`diwanic.embeddings`)
- **Input**: Cleaned JSONL
- **Process**: Generate dense vector embeddings using `intfloat/multilingual-e5-small` (Sentence-Transformers)
- **Output**: JSONL with embeddings (`data/embeddings/poems_with_embeddings.jsonl`)

### Stage 4: Storage (`diwanic.storage` + `diwanic.vectorstore`)
- **Input**: Embedded JSONL
- **Process**:
  - **Postgres**: Store poets, poems, and verses using SQLAlchemy ORM
  - **Qdrant**: Store verse-level and poem-level vectors for similarity search
- **Output**: Persistent data in Postgres and Qdrant collections

### Stage 5: Search Engine (`diwanic.search`)
- **Input**: User query (Arabic)
- **Process**:
  - **Intent Router** (uses 9Router or local LLM) converts query to structured `SearchPlan`
  - **Hybrid Search Engine** executes:
    - Vector search (semantic) on verses and poems
    - Keyword search (fuzzy matching) on poems
    - Reciprocal Rank Fusion (RRF) to combine results
- **Output**: Ranked list of poems/verses with scores

### Stage 6: API & CLI (`diwanic.app` + `diwanic.cli`)
- **API**: FastAPI endpoint (`/api/v2/search`) for programmatic access
- **CLI**: Typer-based commands for ad-hoc search and pipeline execution

## Components

### Configuration
- Centralized in `diwanic.core.config`
- Loads `.env` from repository root
- Static data (poet lists, etc.) in `configs/`

### Infrastructure
- Multi-stage `Dockerfile` and `docker-compose.yml` for running Postgres, Qdrant, and the App locally.
- Thin wrappers for external clients:
  - `diwanic.infrastructure.qdrant`: Qdrant client
  - `diwanic.infrastructure.supabase`: (future) Supabase client

### Orchestration
- Prefect-based pipelines in `diwanic.pipelines`
- Tasks: `scrape_task`, `preprocess_task`, `embed_task`, `ingest_task`
- Flow: `full_pipeline_flow` orchestrates the end-to-end process

### Entry Points
- **API**: `uvicorn diwanic.app.main:app --reload`
- **CLI**: `python -m diwanic.cli <command>`
  - `run-pipeline`: Execute full scraping/processing pipeline
  - `serve`: Start the API server
  - `search`: Perform a hybrid search from the command line

## How to Run Locally

1. **Setup**:
   ```bash
   # Clone repo and enter directory
   cp .env.example .env
   # Edit .env with your database and Qdrant credentials
   pip install -e ".[dev]"
   ```

2. **Run Full Pipeline**:
   ```bash
   make run-flow
   # or
   python -m diwanic.cli run-pipeline
   ```

3. **Start API Server**:
   ```bash
   make run-api
   # or
   uvicorn diwanic.app.main:app --reload
   ```

4. **Search via CLI**:
   ```bash
   python -m diwanic.cli search "الحب والجمال"
   ```

## Running Tests

```bash
make test
# or
pytest -q
```

## Project Structure

```
diwanic/
├── core/           # Configuration, logging
├── app/            # FastAPI wiring, DB session
├── api/            # HTTP routes and models
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic API models
├── search/         # Business logic (router, engine, RRF)
├── scraper/        # Aldiwan.net crawler
├── preprocessing/  # Arabic text cleaning
├── embeddings/     # Vector generation
├── storage/        # Postgres CRUD helpers
├── vectorstore/    # Qdrant interaction
├── infrastructure/ # External service clients
├── utils/          # Helper functions (logger, text splitter)
├── configs/        # Static YAML/JSON (poet lists, etc.)
├── cli/            # Typer-based command-line interface
├── pipelines/      # Prefect flows and tasks
├── tests/          # Unit and integration tests
└── docs/           # Documentation
```

## Decisions & Notes

- **V1 vs V2**: All code is now consolidated under the `diwanic/` package. The legacy V1 directory has been fully removed to eliminate dead code.
- **Hybrid Search**: Combines verse-level vector search (for semantic precision) with poem-level keyword search (for lexical matching) using RRF.
- **Extensibility**: New data sources can be added by implementing a new scraper and updating the pipeline flow.
- **Observability**: Prefect provides built-in retry logic, logging, and a UI for monitoring pipeline runs.

## Contributing

See `CONTRIBUTING.md` (if present) or open an issue/pull request for changes.

## Running in Production

- Use Docker: `make build-docker` then run the container.
- Set environment variables via `.env` or secrets manager.
- Deploy Prefect agent to run the pipeline on schedule.