"""
Generate embedding vectors for cleaned poems.
Usage: ./venv/bin/python scripts/generate_embeddings.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.embeddings.generator import embed_poems

if __name__ == "__main__":
    count = embed_poems("data/processed/poems_cleaned.jsonl", 
                       "data/embeddings/poems_with_embeddings.jsonl")
    print(f"Done: {count} poems embedded.")