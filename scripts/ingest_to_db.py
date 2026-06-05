"""
Ingest cleaned poems from JSONL into PostgreSQL / Supabase.
Usage: ./venv/bin/python scripts/ingest_to_db.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.storage.db_manager import DiwanicDB
from diwanic.core.logger import get_logger

logger = get_logger(__name__)

def ingest_all(jsonl_path: str):
    try:
        db = DiwanicDB()
    except ValueError:
        logger.error("Skipping ingestion: Database not configured.")
        return
        
    logger.info("Setting up database schema...")
    db.init_schema()
    
    logger.info(f"Reading poems from {jsonl_path}...")
    success_count = 0
    error_count = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            poem_data = json.loads(line)
            
            # Extract a pseudo-slug for the poet from the poem_id (e.g. aldiwan_10110 -> aldiwan)
            # Or better, we should probably add poet_slug to scraper later, 
            # for now let's just use the poet name as slug if missing
            if 'poet_slug' not in poem_data:
                poem_data['poet_slug'] = poem_data.get('poet', 'unknown')
                
            try:
                poem_id = db.ingest_poem(poem_data)
                success_count += 1
                if success_count % 10 == 0:
                    logger.info(f"  Ingested {success_count} poems...")
            except Exception as e:
                logger.error(f"  Error on poem {poem_data.get('title')}: {e}")
                error_count += 1
                
    db.close()
    logger.info(f"✅ Ingestion complete. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    PROCESSED_PATH = "data/processed/poems_cleaned.jsonl"
    ingest_all(PROCESSED_PATH)
