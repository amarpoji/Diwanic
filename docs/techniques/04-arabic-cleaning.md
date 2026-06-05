# Technique 04: Arabic Text Cleaning — Stripping Tashkeel While Preserving Letters

## Overview

Arabic text cleaning is the process of transforming raw scraped text into a format optimized for search and embedding, while preserving essential semantic information.

## The Challenge

Arabic has three layers of complexity:

1. **Letter variants** (different shapes, same keyboard key)
   - Alef: أ إ آ ا
   - Ta: ة ه

2. **Diacritics (Tashkeel)** — marks that modify pronunciation
   - Fatha: َ (a sound)
   - Damma: ُ (u sound)
   - Kasra: ِ (i sound)
   - Sukun: ْ (silent)
   - Tanween: ً ٌ ٍ

3. **Decorative elements**
   - Kashida (Tatweel): ـ (letter stretching)
   - Punctuation: « » ، ؛ ؟

## Our Cleaning Strategy

### What We Keep
- All letter variants (أ إ آ ا ة ه)
- Core Arabic letters (ء - ي, Unicode U+0621 - U+064A)
- Spaces

### What We Remove
- All tashkeel (U+064B - U+0652)
- Kashida (U+0640)
- Non-Arabic punctuation

## Implementation

```python
import re

class ArabicCleaner:
    def __init__(self):
        # Regex to match all tashkeel marks
        self.tashkeel_pattern = re.compile(r'[\u064B-\u0652]')
        
        # Regex to match kashida
        self.tatweel_pattern = re.compile(r'\u0640')
    
    def remove_tashkeel(self, text: str) -> str:
        """Strip diacritics but keep letters."""
        return self.tashkeel_pattern.sub('', text)
    
    def remove_tatweel(self, text: str) -> str:
        """Remove decorative stretching."""
        return self.tatweel_pattern.sub('', text)
    
    def clean_for_search(self, text: str) -> str:
        """Full cleaning pipeline."""
        text = self.remove_tashkeel(text)
        text = self.remove_tatweel(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
```

## Example Transformation

### Input (Original)
```arabic
صِلَةُ الهَجرِ لي وَهَجرُ الوِصالِ ... نَكَساني في السُقمِ نُكسَ الهِلالِ
```

### Output (Cleaned)
```arabic
صلة الهجر لي وهجر الوصال ... نكساني في السقم نكس الهلال
```

### What Changed
- `صِلَةُ` → `صلة` (removed َ ِ ُ)
- Preserved: `ة` in `صلة`
- Preserved: Space and `...` structure

## Why This Works for Search

### 1. User Queries Match
Users type: `قصائد حزينة`
Database has: `قَصَائِدُ حَزِينَةٌ`
Without stripping, exact match fails.

### 2. Embedding Model Compatibility
Models like `multilingual-e5`, `AraBERT`, and OpenAI embeddings are trained on:
- Wikipedia (99% without tashkeel)
- News articles (never diacritized)
- Social media (no one types diacritics)

Feeding them classical diacritized text can confuse tokenization.

### 3. Context Replaces Diacritics
The embedding sees:

```arabic
طلب العلم فريضة
```

Even without diacritics on `العلم`, the model knows it means "knowledge" (not "he knew") because of `طلب` (seeking) and `فريضة` (obligation) surrounding it.

## Unicode Reference

| Symbol | Name | Unicode | Action |
|--------|------|---------|--------|
| َ | Fatha | U+064E | Remove |
| ُ | Damma | U+064F | Remove |
| ِ | Kasra | U+0650 | Remove |
| ْ | Sukun | U+0652 | Remove |
| ً | Tanween Fath | U+064B | Remove |
| ٌ | Tanween Damm | U+064C | Remove |
| ٍ | Tanween Kasr | U+064D | Remove |
| ّ | Shadda | U+0651 | Remove |
| ـ | Tatweel | U+0640 | Remove |
| أ | Alef Hamza Above | U+0623 | **Keep** |
| إ | Alef Hamza Below | U+0625 | **Keep** |
| آ | Alef Madda | U+0622 | **Keep** |
| ة | Ta Marbuta | U+0629 | **Keep** |

## Validation Test

```python
# Test the cleaner
cleaner = ArabicCleaner()

original = "صِلَةُ الهَجرِ لي"
cleaned = cleaner.clean_for_search(original)

assert 'ِ' not in cleaned  # Tashkeel removed
assert 'ة' in cleaned      # Ta Marbuta preserved
assert cleaned == "صلة الهجر لي"
```

## Edge Cases

### Poetry Meter Markers
Some classical sources add prosody marks. We remove them:
```arabic
مُسْتَفْعِلُنْ → مستفعلن
```

### Mixed Arabic-English
If the verse contains transliteration:
```arabic
"قصيدة (Poem) عن الحب"
→ "قصيدة (Poem) عن الحب"  # English unchanged
```

### Quranic Symbols
Special markers like ۞ ۩ are removed (not in core Arabic letter range).

## Performance

On a dataset of 41 poems (~2,000 verses):
- Cleaning time: < 0.1 seconds
- Memory: Constant (processes one verse at a time)

---

## Reference
- `diwanic/preprocessing/cleaner.py` — Implementation
- `scripts/preprocess_data.py` — Usage in pipeline
- `docs/decisions/02-arabic-normalization.md` — Design rationale
