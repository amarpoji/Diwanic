# Diwanic: Arabic Poetry RAG Engine

<p align="center">
  <img src="docs/assets/logo.png" alt="Diwanic Logo" width="400">
</p>

*Explore poets you love.*

---

## 📖 Project Overview

**Diwanic** is an intelligent, Retrieval-Augmented Generation (RAG) powered search engine built for classical Arabic poetry. 

**The Problem:** Traditional search engines often fail to understand the deep, metaphorical, and thematic nuances of Arabic poetry. A user looking for a verse about "the sorrow of departure" might get no results if the exact word "departure" isn't present, even if the poet wrote an entire poem about it.

**The Solution:** Diwanic uses AI to bridge the gap between human intent and the vast repository of classical literature. It retrieves contextually relevant verses based on *meaning* rather than just keywords.

**Who is this for?**
- **Researchers & Students**: Looking to explore classical texts through themes rather than static indexing.
- **Developers**: Interested in learning how to build robust, production-ready RAG applications.
- **Arabic Literature Enthusiasts**: Who want to experience a new way to interact with their favorite poets.

---

## 🏗️ High-Level Architecture

The system follows a classic **RAG (Retrieval-Augmented Generation)** flow, ensuring the AI has access to accurate, domain-specific data without hallucinating.

1. **Ingestion**: Raw poetry is scraped and cleaned.
2. **Embedding**: Verses are passed through a multilingual AI model to convert text into numerical vectors (coordinates).
3. **Storage**: Vectors are stored in a **Vector Database** (Qdrant), and poem metadata is stored in **PostgreSQL**.
4. **Retrieval**: When you search, the query is converted into a vector, and we find the most similar poems in the vector space.
5. **Generation**: The retrieved verses provide the context for the **LLM** (DeepSeek) to provide a curated result or analysis.

---

## 🧠 How RAG Works in This Project

Our pipeline transforms unstructured poetry into a searchable knowledge base:

- **Semantic Search**: Unlike keyword matching, we embed verses into a shared vector space where similar concepts live near each other.
- **Intent Routing**: Before searching, the **IntentRouter** analyzes your query to determine if you want to find a specific poem, a poet, or a thematic verse.
- **Hybrid Retrieval**: We combine **Vector Search** (for conceptual matching) with **Text Search** (for exact title or poet name matching) to guarantee accuracy.
- **Context Window**: Retrieved verses are injected into the LLM's prompt, ensuring answers are grounded in our database.

---

## 🛠️ Project Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL
- [Docker](https://www.docker.com/) (For Qdrant and DB management)

### 2. Environment Configuration
Create a `.env` file in the root folder with the following structure:

```env
# Database
DATABASE__URL=postgresql://user:password@host:port/dbname

# Qdrant (Vector Database)
QDRANT__URL=https://your-qdrant-url
QDRANT__API_KEY=your_api_key

# Intelligence Layer (DeepSeek or OpenAI Compatible)
ROUTER__BASE_URL=https://api.deepseek.com
ROUTER__API_KEY=sk-your-api-key

# Optional: Disable logfire if not needed
LOGFIRE_DISABLED=1
```

### 3. Installation
```bash
git clone https://github.com/amarpoji/Diwanic.git
cd Diwanic
python -m venv venv
source venv/bin/activate
pip install -e .
```

---

## 🚀 How to Run the Project

1. **Start Services**: Ensure Docker is running and your `.env` is configured.
2. **Launch UI**:
   ```bash
   make launch-ui
   ```
   *Access the app via `http://localhost:7860` in your browser.*

---

## 📂 Folder Structure

- `/diwanic/app/`: The UI and API bridge (portal).
- `/diwanic/core/`: Global configuration and observability setup.
- `/diwanic/search/`: Core retrieval logic (Hybrid engine + Router).
- `/diwanic/storage/`: Database models and repository logic.
- `/diwanic/pipelines/`: Data ingestion and cleaning scripts.

---

## 🔮 Future Improvements
- **Multimodal Support**: Audio/TTS integration for reciting poems.
- **Discovery Feed**: A smart feed that suggests poems based on your browsing history.
- **Advanced Visualization**: Interactive maps showing how themes migrated across different eras.

---
*Built with ❤️ by Amar.*
