# Troubleshooting 01: ModuleNotFoundError — diwanic Not Found

## The Problem

When running:

```bash
python src/diwanic/scraper/fetcher.py
```

You get:

```
ModuleNotFoundError: No module named 'diwanic'
```

## Why This Happens

Python's module system looks for packages in:
- The current directory
- `PYTHONPATH` environment variable
- Site-packages

If your folder structure looks like:

```
diwanic/                    # Project root
├── src/
│   └── diwanic/           # Package folder
│       ├── scraper/
│       └── core/
```

Then `python src/diwanic/scraper/fetcher.py` won't work because:
1. Python starts in `src/diwanic/scraper/`
2. It looks for `diwanic` there
3. `diwanic` is actually **two levels up** (`../../diwanic/`)

## Solutions

### Solution A: Set PYTHONPATH (Quick Fix)

```bash
# In PowerShell
$env:PYTHONPATH="src"; python src/diwanic/scraper/fetcher.py

# In WSL/Linux
PYTHONPATH=src python src/diwanic/scraper/fetcher.py
```

### Solution B: Flatten the Structure (What We Did)

Move `diwanic/` out of `src/`:

```bash
mv src/diwanic ./
```

Now the structure is:

```
diwanic/                    # Project root + Package folder
├── scraper/
├── core/
└── ...
```

Then run as a module:

```bash
python -m diwanic.scraper.fetcher
```

### Solution C: Install as Package (For Production)

```
pip install -e .
```

This makes Python always find `diwanic`, regardless of working directory.

## Our Chosen Solution

We went with **Solution B + Module Execution**:

```bash
python -m diwanic.scraper.fetcher
```

Why?
- No environment variables needed
- Works from any subdirectory
- Follows Python best practices

## How to Run Scripts Now

Always use `-m` (module) syntax:

```bash
# Scraper test
python -m diwanic.scraper.fetcher

# Scrape all poems
python -m scripts.scrape_all

# Preprocess
python -m scripts.preprocess_data

# Discover poet
python -m scripts.discover_poet https://www.aldiwan.net/cat-poet-Mutanabi
```

## What Changed

Before:

```bash
# This failed
python src/diwanic/scraper/fetcher.py
```

After:

```bash
# This works
python -m diwanic.scraper.fetcher
```

## Summary

- **Root cause**: Python couldn't find the package because it was inside `src/`
- **Fix**: Flatten structure, use `-m` flag
- **Best practice**: Run `python -m <module>` instead of `python <path/to/file.py>`

---

## See Also
- `decisions/03-flat-structure.md` — Why we flattened the folder
- `diwanic_plan.md` — Project roadmap
