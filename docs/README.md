# 📖 Diwanic — Project Knowledge Base

## Structure

```
docs/
├── README.md              ← You are here
├── decisions/             ← Why we chose what we chose
├── techniques/            ← How each component works
├── troubleshooting/       ← Problems we faced and fixed
└── architecture/          ← System diagrams and data flow
```

---

## 📁 decisions/
**Why we made the choices we did.**

| Document | Topic |
|----------|-------|
| 01-schema-design.md | Why we chose JSONL over JSON, what fields are required |
| 02-arabic-normalization.md | Why we keep Alef variants but strip diacritics |
| 03-flat-structure.md | Why diwanic/ sits in project root, not in src/ |
| 04-poet-config.md | Why we use YAML for poet management |
| 05-encoding-choice.md | Why UTF-8, not windows-1256 for Arabic |

## 📁 techniques/
**How each component works.**

| Document | Topic |
|----------|-------|
| 01-scraping-with-retry.md | Polite scraping with exponential backoff |
| 02-html-parsing.md | Extracting verses from Aldiwan.net H3 elements |
| 03-schema-validation.md | Ensuring every poem has required fields |
| 04-arabic-cleaning.md | Stripping tashkeel while preserving letter forms |
| 05-jsonl-format.md | Why one poem per line beats a giant JSON array |

## 📁 troubleshooting/
**Problems we encountered and how we fixed them.**

| Document | Issue |
|----------|-------|
| 01-module-not-found.md | Fixing PYTHONPATH when running scripts |
| 02-poem10111-failure.md | Parsing poems with 0 verses |
| 03-encoding-garbled-text.md | Fixing UTF-8 vs windows-1256 confusion |
| 04-404-poet-slugs.md | Finding correct Aldiwan.net slugs |
| 05-mahmoud-darwish-parsing.md | Modern poet pages with different structure |

## 📁 architecture/
**System design.**

| Document | Topic |
|----------|-------|
| 01-data-flow.md | From website → scraper → cleaner → embeddings → search |
| 02-folder-structure.md | Why every folder exists |
