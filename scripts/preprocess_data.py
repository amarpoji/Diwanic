"""
Clean and preprocess scraped poems.
Usage: ./venv/bin/python scripts/preprocess_data.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.preprocessing.pipeline import process_poems

if __name__ == "__main__":
    process_poems("data/raw/poems_all.jsonl", "data/processed/poems_cleaned.jsonl")