# Architecture 01: Data Flow — From Website to Search

## High-Level Pipeline

```
┌─────────────────┐
│  Aldiwan.net    │ ← Source of truth
└────────┬────────┘
         │ HTTP GET
         ▼
┌─────────────────────────────────────┐
│ Phase 1: SCRAPER                    │
│ • fetcher.py — HTTP + retry logic   │
│ • parser.py — Extract from HTML     │
│ • models.py — Validate schema       │
└────────┬────────────────────────────┘
         │ JSONL (raw)
         ▼
    data/raw/
    poems_all.jsonl
    (41 poems, 149KB)
         │
         │ Poem validation
         │ (41 input → 41 valid → 41 saved)
         │
┌─────────────────────────────────────┐
│ Phase 2: PREPROCESSING              │
│ • cleaner.py — Strip tashkeel       │
│ • Add searchable_text field         │
│ • Add original_text field           │
└────────┬────────────────────────────┘
         │ JSONL (cleaned)
         ▼
    data/processed/
    poems_cleaned.jsonl
    (41 poems, 374KB)
         │
         │ Each poem now has:
         │ • original_text (with diacritics)
         │ • searchable_text (stripped)
         │
┌─────────────────────────────────────┐
│ Phase 3: EMBEDDINGS (Next)          │
│ • Load poems_cleaned.jsonl          │
│ • For each searchable_text:         │
│   - Generate vector (768d or 1024d) │
│   - Store with poem metadata        │
└────────┬────────────────────────────┘
         │ Embeddings + metadata
         ▼
    data/embeddings/
    poems_vectors.jsonl or .parquet
         │
         │ Load into vector DB
         │
┌─────────────────────────────────────┐
│ Phase 4: VECTOR DATABASE (Qdrant)   │
│ Collections:                        │
│ • poems_collection (dense vectors)  │
│ • poems_metadata (poet, era, etc.)  │
└────────┬────────────────────────────┘
         │
         │ 1. Vector search
         │ 2. Keyword search (BM25)
         │ 3. Hybrid fusion
         │
┌─────────────────────────────────────┐
│ Phase 5: API (FastAPI)              │
│ GET /search?q=قصائد+عن+الفراق       │
│ Returns: Top 10 poems               │
│   - original_text (display)         │
│   - poet, era, meter (metadata)     │
│   - similarity score                │
└─────────────────────────────────────┘
         │
         ▼
      Frontend / User
```

## Data at Each Stage

### After Scraping (Phase 1)
```json
{
  "poem_id": "aldiwan_10110",
  "title": "صلة الهجر لي وهجر الوصال",
  "poet": "المتنبي",
  "verses": [
    "صِلَةُ الهَجرِ لي ... نَكَساني في السُقمِ",
    "فَغَدا الجِسمُ ناقِصاً ..."
  ],
  "source_url": "https://www.aldiwan.net/poem10110.html",
  "website": "aldiwan",
  "scraped_at": "2026-06-02T10:28:50Z",
  "era": "العصر العباسي",
  "meter": "الخفيف"
}
```

### After Preprocessing (Phase 2)
```json
{
  "poem_id": "aldiwan_10110",
  "title": "صلة الهجر لي وهجر الوصال",
  "poet": "المتنبي",
  "title_searchable": "صلة الهجر لي وهجر الوصال",
  "poet_searchable": "المتنبي",
  "original_text": "صِلَةُ الهَجرِ لي وَهَجرُ الوِصالِ ... نَكَساني في السُقمِ نُكسَ الهِلالِ\nفَغَدا الجِسمُ ناقِصاً ...",
  "searchable_text": "صلة الهجر لي وهجر الوصال ... نكساني في السقم نكس الهلال\nفغدا الجسم ناقصا ...",
  "verses": [...],
  ... (other fields)
}
```

### After Embedding (Phase 3)
```json
{
  "poem_id": "aldiwan_10110",
  "embedding": [0.123, -0.456, 0.789, ...],  // 768 dimensions
  "title": "صلة الهجر لي وهجر الوصال",
  "poet": "المتنبي",
  "era": "العصر العباسي",
  "searchable_text": "صلة الهجر لي وهجر الوصال ..."
}
```

## Decisions Made at Each Stage

| Stage | Decision | Reason |
|-------|----------|--------|
| Scraping | JSONL format | Memory efficient, append-only |
| Scraping | Validation before save | No garbage data in dataset |
| Preprocessing | Keep `original_text` | Display quality, meter analysis |
| Preprocessing | Create `searchable_text` | Search/embedding quality |
| Embedding | Store with metadata | Filtering by poet/era in search |
| Vector DB | Qdrant | Hybrid search, good Arabic support |
| API | FastAPI | Fast, async, auto-docs |

## Error Handling at Each Stage

### Stage 1: Scraping
- HTTP 404? Skip that poem, log warning
- Parser fails? Validation catches it
- 0 verses? Reject before save

### Stage 2: Preprocessing
- Missing `verses` field? Fill with empty list
- Invalid UTF-8? Already handled (forced UTF-8 in scraper)

### Stage 3: Embedding
- Empty text? Skip or use placeholder
- Model error? Retry with fallback model

### Stage 4: Vector DB
- Insert fails? Transaction rollback
- Query timeout? Return partial results

### Stage 5: API
- Invalid query? Return 400 Bad Request
- DB down? Return 503 Service Unavailable

---

## Reference
- `diwanic_plan.md` — Full project roadmap
- Individual phase docs in `techniques/` and `decisions/`
