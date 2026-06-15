# Diwanic V2 Documentation

Welcome to the **Version 2.0 (Agentic RAG)** documentation for Diwanic. 

V2 represents the transition from a "Search Engine" to an "Agentic AI System." This folder documents our journey from raw SQL to SQLAlchemy, and from simple keyword matching to an LLM-driven Intent Router.

---

## 🗺️ Navigation

### [01. Architecture](./01-architecture/01-overview.md)
The big picture: How the Brain (9Router) connects to the Memory (Postgres/Qdrant).

### [02. Stages](./02-stages/01-config-and-database.md)
Step-by-step documentation of how we built the V2 layer by layer.

### [03. Problems & Solutions](./03-problems/01-9router-instructor.md)
Detailed post-mortems of every bug we faced and how we solved them.

### [04. Design Decisions](./04-decisions/01-raw-json-over-instructor.md)
The "Why" behind our technical choices (e.g., why we dropped Instructor).

### [05. References](./05-references/01-9router-setup.md)
Quick guides for environment setup and 9Router configuration.

---

## 🚀 V2 Status
| Component | Status | Tech |
| :--- | :--- | :--- |
| **Config/DB** | ✅ Done | SQLAlchemy + .env |
| **Schemas** | ✅ Done | Pydantic V2 |
| **Router** | ✅ Done | 9Router (Local Proxy) |
| **Search Engine** | ✅ Done | SQL (ILIKE) + Per-word Scoring |
| **API** | ✅ Done | FastAPI + Pydantic Response |
| **Vector Search** | ⏳ Planned | Qdrant Hybrid Fusion |
| **Verse Retrieval** | ⏳ Planned | Semantic Chunking |
