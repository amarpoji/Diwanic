# Decision 03: Folder Structure — Why `diwanic/` in Root

## The Question

Why did we move the `diwanic/` package folder from:

```
src/
└── diwanic/
    ├── scraper/
    └── core/
```

to:

```
diwanic/
├── scraper/
└── core/
```

## The Problem with Nested Structure

### 1. Python Cannot Find the Package

When running:

```bash
python -m diwanic.scraper.fetcher
```

Python looks for a package named `diwanic` in:
- The current directory
- Paths in `PYTHONPATH`
- Installed site-packages

If `diwanic` is inside `src/`, Python doesn't see it unless you set `PYTHONPATH=src`.

### 2. Module Imports Become Awkward

In `src/diwanic/scraper/fetcher.py`, you'd need:

```python
import sys
sys.path.insert(0, '../..')  # Ugly workaround
from diwanic.core.logger import get_logger
```

### 3. Test Scripts Get Complicated

```bash
# Before (nested)
PYTHONPATH=src python -m diwanic.scraper.fetcher

# After (flat)
python -m diwanic.scraper.fetcher
```

## Why We Chose Flat Structure

### 1. Clean Module Execution

```
python -m diwanic.scraper.fetcher
python -m scripts.preprocess_data
python -m scripts.scrape_all
```

No environment variables. No path manipulation. Works out of the box.

### 2. Standard Python Packaging

This matches the standard structure for Python packages:

```
project-root/
├── package-name/      ← Your code
│   └── __init__.py
├── scripts/           ← CLI entrypoints
└── docs/              ← Documentation
```

### 3. Future-Proof for Distribution

If you want to publish to PyPI later, flat structure is required:

```bash
# Standard layout for pip install .
project-root/
├── setup.py
├── diwanic/          ← The package
│   ├── __init__.py
│   ├── scraper/
│   └── preprocessing/
└── scripts/
```

## Current Structure

```
diwanic/                          ← Project root + Package folder
├── diwanic/                      ← Python package (import diwanic)
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── config.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── fetcher.py
│   │   ├── parser.py
│   │   ├── models.py
│   │   └── utils.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── cleaner.py
│   └── ...
├── scripts/                      ← CLI tools
│   ├── scrape_all.py
│   ├── preprocess_data.py
│   └── discover_poet.py
├── docs/                         ← Knowledge base
│   ├── README.md
│   ├── decisions/
│   ├── techniques/
│   └── troubleshooting/
├── data/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── configs/
│   └── poets.yaml
├── venv/                         ← Virtual environment
└── requirements.txt
```

## Trade-offs

| Aspect | Nested (src/) | Flat (root) |
|--------|---------------|-------------|
| Import simplicity | ❌ Needs PYTHONPATH | ✅ Clean `python -m` |
| IDE support | ✅ Better for some IDEs | ✅ Standard works fine |
| Future PyPI | ❌ Needs restructuring | ✅ Ready to go |
| Single package | ❌ Harder | ✅ Natural |

## The `src/` Folder Dilemma

Some projects use `src/` to prevent accidental imports during development. But for Diwanic:

- We're not building a library for others to import
- We want simple CLI scripts
- The flat structure wins for simplicity

If in the future we need `src/` (e.g., building a pip package), we can add it back with proper `setup.py`.

---

## Reference
- `docs/troubleshooting/01-module-not-found.md` — The original problem and fix
- `requirements.txt` — Dependencies list
- `diwanic_plan.md` — Project roadmap
