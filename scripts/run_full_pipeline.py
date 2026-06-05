"""
Run the full Diwanic pipeline end-to-end:
Scrape → Preprocess → Embed → (future: Load to Qdrant)

Usage:
    ./venv/bin/python scripts/run_full_pipeline.py
    ./venv/bin/python scripts/run_full_pipeline.py --poems 50
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.core.logger import get_logger
from diwanic.scraper.pipeline import scrape_all_poets, save_poems
from diwanic.preprocessing.pipeline import process_poems
from diwanic.embeddings.generator import embed_poems

logger = get_logger(__name__)


def run_stage(name: str, func, *args, **kwargs):
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"\n{'='*60}")
    logger.info(f"  STAGE: {name}")
    logger.info(f"{'='*60}")
    start = time.time()
    
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"  '{name}' completed in {elapsed:.1f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"  '{name}' FAILED after {elapsed:.1f}s: {e}")
        raise


def run_full_pipeline(
    max_poems_per_poet: int = 30,
    config_path: str = "configs/poets.yaml",
    raw_path: str = "data/raw/poems_all.jsonl",
    processed_path: str = "data/processed/poems_cleaned.jsonl",
    embeddings_path: str = "data/embeddings/poems_with_embeddings.jsonl",
):
    """Run the complete Diwanic pipeline from scrape to embeddings."""
    
    total_start = time.time()
    
    logger.info("")
    logger.info("╔══════════════════════════════════════╗")
    logger.info("║     DIWANIC FULL PIPELINE           ║")
    logger.info("╚══════════════════════════════════════╝")
    logger.info(f"  Max poems per poet: {max_poems_per_poet}")
    logger.info("")
    
    # Stage 1: Scrape
    poems = run_stage("Scraping", scrape_all_poets,
                      config_path, max_poems_per_poet)
    
    run_stage("Saving raw poems", save_poems, poems, raw_path)
    
    if not poems:
        logger.error("No poems scraped. Pipeline aborted.")
        return
    
    # Stage 2: Preprocess
    run_stage("Preprocessing (clean + normalize)",
              process_poems, raw_path, processed_path)
    
    # Stage 3: Embeddings
    run_stage("Generating embedding vectors",
              embed_poems, processed_path, embeddings_path)
    
    # Summary
    total_elapsed = time.time() - total_start
    logger.info("")
    logger.info("╔══════════════════════════════════════╗")
    logger.info("║     PIPELINE COMPLETE                ║")
    logger.info("╚══════════════════════════════════════╝")
    logger.info(f"  Total time:      {total_elapsed:.1f}s")
    logger.info(f"  Poems scraped:   {len(poems)}")
    logger.info(f"  Raw data:        {raw_path}")
    logger.info(f"  Cleaned data:    {processed_path}")
    logger.info(f"  Embeddings:      {embeddings_path}")
    logger.info("")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the full Diwanic pipeline")
    parser.add_argument("--poems", type=int, default=30,
                      help="Max poems per poet (default: 30)")
    
    args = parser.parse_args()
    run_full_pipeline(max_poems_per_poet=args.poems)
