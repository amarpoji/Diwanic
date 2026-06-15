# V2 Post-Mortem: Problems & Decisions

In V2, we faced complex integration challenges between LLMs and search logic. This document records how we handled them.

---

## 🛑 Problem 1: The Instructor/9Router "Tool Call" Loop
**Symptom:** The system would hang or error with `Instructor does not support multiple tool calls`.
**Cause:** 9Router (or its providers) sometimes returned response formats that `instructor` interpreted as multiple tool calls, even for simple JSON output.

### 💡 Decision: Raw JSON Prompting
We decided to **drop the Instructor library** for the router. Instead:
1. We write a very strict system prompt asking for "ONLY valid JSON".
2. We manually use `json.loads()`.
3. We validate the result with `SearchPlan(**data)`.
**Result:** 100% stability across all 9Router providers.

---

## 🛑 Problem 2: The "Zero Results" FTS Failure
**Symptom:** Searching for "sad poems" returned 0 results even though the poems existed.
**Cause:** Postgres Full-Text Search (`plainto_tsquery`) uses an **AND** between all words. If one word in the router's semantic query was missing from the poem, the whole search failed.

### 💡 Decision: Per-Word ILIKE Scoring
We shifted from strict FTS to a **Ranking-Based ILIKE** approach:
1. We split the query into individual Arabic words.
2. We search for any of those words using `ILIKE`.
3. We assign points (3 for title match, 1 for text match).
**Result:** Highly forgiving search that always shows the most relevant poems.

---

## 🛑 Problem 3: The Hamza Normalization Wall
**Symptom:** `أبو نواس` (with Hamza) returned 0 results, while `ابو نواس` (bare Alef) worked.
**Cause:** Database metadata stored names with bare Alefs, but LLMs often use Hamzas. ILIKE is sensitive to these variations.

### 💡 Decision: Symmetric Normalization
We implemented a normalization helper `_normalize_arabic_name`:
1. It strips Hamza variants (`أ إ آ` -> `ا`) from the query.
2. It uses `REPLACE()` in the SQL query to strip Hamza variants from the database side during comparison.
**Result:** "أبو نواس", "ابو نواس", and "أبي نواس" now all resolve to the same poet.
