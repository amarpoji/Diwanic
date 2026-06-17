# Diwanic: Arabic Poetry RAG Engine

<p align="center">
  <img src="docs/assets/logo.png" alt="Diwanic Logo" width="1080">
</p>

*Explore poets you love.*

---

## 📖 Project Overview
**Diwanic** is an intelligent, Retrieval-Augmented Generation (RAG) powered search engine built for classical Arabic poetry. It helps researchers and enthusiasts explore the deep, thematic nuances of classical texts through semantic discovery rather than static keyword matching.

---

## 🏗️ Architecture & Data Flow

Diwanic transforms unstructured web data into an intelligent knowledge base through a structured pipeline.

### High-Level Flow
```mermaid
graph TD
    A[aldiwan.net] -->|Scraper| B(Raw Data)
    B -->|Preprocessor| C(Cleaned Verses)
    C -->|Embedding Model| D[Vector Space]
    D --> E[(Qdrant Vector DB)]
    C --> F[(PostgreSQL Metadata)]
    
    G[User Query] --> H{Intent Router}
    H -->|Concept| I[Semantic Search]
    H -->|Name/Title| J[Text Search]
    I --> E
    J --> F
    K[Final Result]
```

### Data Pipeline Details
1. **Scraping**: The scraper module fetches raw content from *aldiwan.net*.
2. **Preprocessing**: Normalizes Arabic script, cleans HTML, and structures verses into poet/era objects.
3. **Ingestion**: 
   - **Vector DB (Qdrant)**: Stores embeddings for semantic "meaning-based" search.
   - **SQL DB (PostgreSQL)**: Stores original text and metadata for reliable retrieval.

---

## 📥 Getting Data from the Web
To populate the engine with poetry:

1. **Configure Scraper**: Adjust `diwanic/scraper/fetcher.py` if necessary.
2. **Run Pipeline**:
   You can trigger the ingestion pipeline directly using the provided Makefile command:
   ```bash
   make run-flow
   ```
   *This command runs the `full_pipeline_flow`, which automatically fetches, processes, and embeds the poetry data.*

---

## 🛠️ Usage with `make`

The `Makefile` simplifies daily operations. Here are the core commands:

| Command | Description |
| :--- | :--- |
| `make install` | Installs project dependencies in editable mode. |
| `make run-flow` | **Fetches/Ingests data** from the web and updates your databases. |
| `make launch-ui` | Launches the Gradio web interface. |
| `make test` | Runs the test suite to ensure system integrity. |
| `make clean` | Removes caches and temporary build files. |

---

## 🧠 How RAG Works in This Project
1. **Vectorization**: Every poem is converted into a vector (a list of numbers) representing its semantic meaning.
2. **Hybrid Retrieval**:
   - **Semantic**: We use `multilingual-e5-small` to match concepts (e.g., searching "sadness" finds verses about "crying").
   - **Keyword**: We use SQL `LIKE` for precise title/author matches.
3. **Context Construction**: When you ask a question, we combine your search with the retrieved verses and send them to the LLM (DeepSeek) to provide an insightful response.

---

## 🚀 Setup Guide

### 1. Requirements
- Python 3.10+, Docker, PostgreSQL.

### 2. Configuration (`.env`)
Create a `.env` file in the root:
```env
DATABASE__URL=postgresql://user:pass@localhost:5432/diwanic
QDRANT__URL=https://<your-qdrant-cloud-url>
QDRANT__API_KEY=<your-key>
ROUTER__API_KEY=<your-deepseek-key>
LOGFIRE_DISABLED=1
```

### 3. Quick Start
```bash
# 1. Install
make install

# 2. Ingest Poetry (Scrape data)
make run-flow

# 3. Launch the Search Engine
make launch-ui
```
*Access the UI at `http://127.0.0.1:7860`.*

---

## 📂 Folder Structure
- `diwanic/app/`: UI and search bridge.
- `diwanic/scraper/`: Web scraping logic.
- `diwanic/pipelines/`: Data cleaning and ingestion flows.
- `diwanic/search/`: Core hybrid retrieval logic.
- `diwanic/storage/`: Database repositories.

---

*Built with ❤️ by Amar.*
