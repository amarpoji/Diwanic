# Decision 01: Schema Design — JSONL vs JSON

## The Question
How should we store scraped poem data? Single JSON array or JSONL (one object per line)?

## The Decision
**JSONL (JSON Lines)** — one poem per line.

## Why JSONL?

### 1. **Streaming & Memory Efficiency**
- **Single JSON**: Must load entire file into RAM. With 10,000 poems, this could be 500MB+.
- **JSONL**: Read one line at a time. Constant memory usage no matter how many poems you have.

```python
# JSONL approach (memory-friendly)
with open('poems.jsonl') as f:
    for line in f:
        poem = json.loads(line)
        process(poem)  # Process one at a time
```

### 2. **Append-Only Growth**
With JSONL, adding new poems is trivial—just append a new line. No need to reparse the whole file.

```python
# Add 100 new poems
with open('poems.jsonl', 'a') as f:
    for poem in new_poems:
        f.write(json.dumps(poem, ensure_ascii=False) + '\n')
```

### 3. **Parallel Processing**
JSONL works naturally with MapReduce-style frameworks (Spark, Pandas apply). You can split the file by lines and process chunks in parallel.

### 4. **Industry Standard for ML**
HuggingFace datasets, Weights & Biases, and most ML platforms use JSONL. It's the lingua franca of data pipelines.

## Schema Fields (Required)

Every poem **must** have:

| Field | Type | Example | Why |
|-------|------|---------|-----|
| `poem_id` | string | `aldiwan_71682` | Unique, stable identifier |
| `title` | string | `خذ في البكا` | Display + search |
| `poet` | string | `المتنبي` | Filtering, display |
| `verses` | list[str] | `["البيت الأول...", "البيت الثاني..."]` | Core content |
| `source_url` | string | `https://www.aldiwan.net/poem71682.html` | Traceability |
| `website` | string | `aldiwan` | Multi-source support (future) |
| `scraped_at` | ISO string | `2026-06-02T10:28:50Z` | Freshness tracking |

Optional metadata:
- `era`, `meter`, `rhyme`, `category`, `original_text`, `searchable_text`

## What Happens If a Poem Fails Validation?

See `troubleshooting/01-module-not-found.md` for the filtering logic. Briefly: if a poem has 0 verses, it's rejected before saving.

## Trade-offs

| Aspect | JSONL | Single JSON |
|--------|-------|------------|
| Memory | ✅ Low | ❌ High |
| Query by ID | ❌ Slow (must scan) | ✅ Fast (parse once) |
| Append | ✅ Easy | ❌ Hard |
| Human-readable | ✅ Each line | ✅ Whole file |

For Diwanic, **JSONL wins** because we append data frequently and work with large collections.

---

## Reference
- `data/raw/poems_all.jsonl` — Our raw scraped poems
- `data/processed/poems_cleaned.jsonl` — Cleaned poems ready for embedding
