# Troubleshooting 05: "Why Are There Still Diacritics?" — Understanding the Two-Field Design

## The Problem

After preprocessing, you open `data/processed/poems_cleaned.jsonl` and see:

```arabic
صِلَةُ الهَجرِ لي وَهَجرُ الوِصالِ
```

But we said we stripped diacritics! What happened?

## The Answer

You're looking at the **wrong field**.

Each poem in `poems_cleaned.jsonl` has **two** text fields:

```json
{
  "poem_id": "aldiwan_10110",
  "title": "صلة الهجر لي وهجر الوصال",
  "original_text": "صِلَةُ الهَجرِ لي وَهَجرُ الوِصالِ ... نَكَساني في السُقمِ",
  "searchable_text": "صلة الهجر لي وهجر الوصال ... نكساني في السقم",
  "verses": [...]
}
```

### ✅ `searchable_text` — CLEANED (no diacritics)
This is what we use for:
- Embedding (feed to the model)
- Keyword search (BM25)
- Any ML pipeline

### ✅ `original_text` — PRESERVED (has diacritics)
This is what we use for:
- Displaying to users
- Meter analysis
- Academic study

## Why Two Fields?

**Search quality** vs. **Display quality** are different:

1. **For Search**: We need clean text without diacritics because:
   - Users don't type diacritics
   - Embedding models are trained on undiacritized text
   - Cleaner input = better vector representations

2. **For Display**: We need the original beautiful text because:
   - Poetry is meant to be read with proper pronunciation marks
   - Scholars need to see the meter and rhyme
   - Classical Arabic looks better with tashkeel

## How to Verify

### Check `searchable_text` (should be clean)
```bash
./venv/bin/python -c "
import json
with open('data/processed/poems_cleaned.jsonl') as f:
    poem = json.loads(f.readline())
    print('SEARCHABLE:', poem['searchable_text'][:100])
"
```

Output: `صلة الهجر لي وهجر الوصال` ✅ No diacritics

### Check `original_text` (should have diacritics)
```bash
./venv/bin/python -c "
import json
with open('data/processed/poems_cleaned.jsonl') as f:
    poem = json.loads(f.readline())
    print('ORIGINAL:', poem['original_text'][:100])
"
```

Output: `صِلَةُ الهَجرِ لي وَهَجرُ` ✅ Has diacritics

## When Building the API

Your FastAPI response should use `original_text`:

```python
@app.get("/search")
async def search_poems(q: str):
    results = hybrid_search(q)
    
    return [
        {
            "title": poem["title"],
            "original_text": poem["original_text"],  # ← Display this
            "poet": poem["poet"],
            "era": poem["era"],
            "similarity_score": score
        }
        for poem, score in results
    ]
```

But internally, the search uses `searchable_text`:

```python
def hybrid_search(query: str):
    # 1. Clean the query
    cleaned_query = cleaner.clean_for_search(query)
    
    # 2. Generate embedding from cleaned query
    query_embedding = model.encode(cleaned_query)
    
    # 3. Search Qdrant using cleaned embeddings
    # (Qdrant indexed using searchable_text)
    results = qdrant_client.search(query_embedding)
    
    return results
```

---

## Key Takeaway

✅ **The diacritics are correctly stripped in `searchable_text`.**

If you see diacritics when you view the file, you're looking at `original_text` or `verses` field, which we **intentionally** preserve for quality display.

---

## Reference
- `docs/decisions/02-arabic-normalization.md` — Why we keep two versions
- `diwanic/preprocessing/cleaner.py` — The cleaning logic
