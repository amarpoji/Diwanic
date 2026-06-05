"""
Scrape poems from all poets in config.
Usage: ./venv/bin/python scripts/scrape_all.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.scraper.pipeline import scrape_all_poets, save_poems

if __name__ == "__main__":
    poems = scrape_all_poets(max_poems_per_poet=30)
    save_poems(poems, "data/raw/poems_all.jsonl")
    print(f"Done: {len(poems)} poems saved.")
