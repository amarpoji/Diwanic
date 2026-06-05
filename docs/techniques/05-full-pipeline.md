# Pipeline Documentation

## Running the Full Pipeline

The `run_full_pipeline.py` script automates the entire Diwanic workflow from scraping to embeddings.

### Quick Start

```bash
# Run with default settings (30 poems per poet)
./venv/bin/python scripts/run_full_pipeline.py

# Run with custom poem count
./venv/bin/python scripts/run_full_pipeline.py --poems 50
```

### What It Does

**Stage 1: Scraping**
- Reads poet list from `configs/poets.yaml`
- Scrapes poems from Aldiwan.net
- Validates each poem against schema
- Saves to `data/raw/poems_all.jsonl`

**Stage 2: Preprocessing**
- Loads raw poems from JSONL
- Removes diacritics (tashkeel) → `searchable_text`
- Preserves original text → `original_text`
- Saves to `data/processed/poems_cleaned.jsonl`

**Stage 3: Embedding**
- Loads cleaned poems
- Generates 384-dimensional vectors using `intfloat/multilingual-e5-small`
- Adds `embedding` field to each poem
- Saves to `data/embeddings/poems_with_embeddings.jsonl`

### Output Files

| File | Location | Purpose |
|------|----------|---------|
| Raw | `data/raw/poems_all.jsonl` | Original scraped data |
| Cleaned | `data/processed/poems_cleaned.jsonl` | Normalized for search |
| Embeddings | `data/embeddings/poems_with_embeddings.jsonl` | Vectors ready for Qdrant |

### Error Handling

If a stage fails:
1. The pipeline stops immediately
2. Error is logged with timestamp
3. You can fix the issue and re-run
4. Previous stages are skipped (cached results reused)

### Timing

- **Scraping**: ~1-2 seconds per poem (polite delays)
- **Preprocessing**: ~0.5 seconds per poem
- **Embedding**: ~5-10 seconds per poem (first run downloads model)

For 30 poems per poet (6 poets = 180 poems):
- Total: ~30-40 minutes

### Next Steps

After the pipeline completes:
1. Load embeddings into Qdrant (Phase 4)
2. Build hybrid search (Phase 5)
3. Deploy FastAPI (Phase 6)
