# Decision 02: Arabic Normalization — What to Preserve vs. Strip

## The Question
Arabic has letter variants and diacritics:
- Alef variants: أ (hamza above), إ (hamza below), آ (madda), ا (bare)
- Ta Marbuta: ة (closed), ه (open)
- Diacritics (tashkeel): َ ُ ِ ٌ ٍ ْ etc.

Which should we preserve for search? Which should we remove?

## The Decision
**Preserve letter forms, strip diacritics.**

### 1. Preserve Alef Variants (أ إ آ)
Why? They are different letters with different sounds and meanings.

```arabic
أكل (he ate)
إلى (to/until)
آخر (last/another)
```

In native Arabic typing, people always type the correct Alef variant. A search query like `أكل` will never match a verse containing `إلى`.

### 2. Preserve Ta Marbuta (ة)
Why? The same reason: it's a distinct letter.

```arabic
مكتبة (library) → مكتبه (his desk) — completely different words
شجرة (tree) → شجره (his bravery)
```

### 3. Strip Diacritics (Tashkeel: َ ُ ِ ٌ ٍ ْ)
Why? Because real-world Arabic is written without them.

- **User expectation**: People search without diacritics.
- **Embedding models**: Trained on undiacritized text (news, web, Wikipedia).
- **Context carries the meaning**: The embedding sees surrounding words.

Example of why we strip:
```arabic
عَلِمَ (he knew)
عُلِّمَ (he was taught)
عِلْم (knowledge)
```

All share the base letters `علم`. The embedding model uses the verse context to figure out which one it is.

## Implementation

Our `ArabicCleaner` class in `diwanic/preprocessing/cleaner.py`:

```python
def clean_for_search(self, text: str) -> str:
    # Keep all letter forms
    # Remove only tashkeel (harakat: َ ُ ِ ٌ ٍ ْ)
    text = self.tashkeel_pattern.sub('', text)
    return text
```

## Two Text Fields

We store both versions:

| Field | Contains | Use Case |
|-------|----------|----------|
| `original_text` | Full verse with diacritics | Display to users, meter analysis |
| `searchable_text` | Stripped of diacritics | Embedding, keyword search |

## Edge Cases We Handle

### Kashida (Tatweel: ـ)
We remove it. It's just visual stretching.

```arabic
عــــرب → عرب  # Same word
```

### Punctuation
Removed—not useful for semantic search.

```arabic
« ، . : ! ؟ » → removed
```

### Whitespace
Normalized (multiple spaces → single space).

## What This Means for Retrieval Quality

When a user searches "قصائد عن الفراق":

- **Good**: The model sees the words without diacritics (`قصائد`, `فراق`) — matches training data.
- **Good**: If the query had an Alef variant, it's preserved (`إن`, `أو`, `آ`).
- **Bad**: Search for `عَلِمَ` won't find exact match, but semantic search will find `علم` context.

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Keep everything** | Perfect for display | Poor search recall (user types differently) |
| **Full normalization** | High recall | Loss of semantic meaning (أ ≠ إ ≠ آ ≠ ا) |
| **Our approach** | Balance between recall and meaning | Slightly more complex |

Our approach matches **how Arabic is actually used**: typed letters matter, diacritics don't.

---

## Reference
- `diwanic/preprocessing/cleaner.py` — The cleaner class
- `scripts/preprocess_data.py` — Pipeline that creates both fields
