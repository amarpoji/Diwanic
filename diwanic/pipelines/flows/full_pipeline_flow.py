"""Prefect flow for the full Diwanic pipeline."""
from pathlib import Path
from prefect import flow
from diwanic.pipelines.tasks.scrape_task import scrape_poets_task
from diwanic.pipelines.tasks.preprocess_task import preprocess_poems_task
from diwanic.pipelines.tasks.embed_task import embed_poems_task
from diwanic.pipelines.tasks.ingest_task import ingest_poems_task

@flow(name="Diwanic Full Pipeline")
def full_pipeline_flow(
    poets_config: str = "configs/poets.yaml",
    max_poems: int = 30,
    raw_path: str = "data/raw/poems_all.jsonl",
    processed_path: str = "data/processed/poems_cleaned.jsonl",
    embeddings_path: str = "data/embeddings/poems_with_embeddings.jsonl",
    skip_existing: bool = False,
):
    """
    Orchestrate the Diwanic data pipeline:
    Scrape -> Preprocess -> Embed -> Ingest
    If skip_existing=True, each step will check for previous output files
    and skip the step if the file already exists and is non‑empty.
    """
    # 1. Scrape (skip if file already exists)
    if not skip_existing or not Path(raw_path).exists() or Path(raw_path).stat().st_size == 0:
        scrape_poets_task(config_path=poets_config, max_poems_per_poet=max_poems, output_path=raw_path)
    else:
        print(f"🔹 Skipping scrape – {raw_path} already exists")
    
    # 2. Preprocess (skip if processed file exists)
    if not skip_existing or not Path(processed_path).exists() or Path(processed_path).stat().st_size == 0:
        preprocess_poems_task(input_path=raw_path, output_path=processed_path)
    else:
        print(f"🔹 Skipping preprocess – {processed_path} already exists")
    
    # 3. Embed (skip if embeddings file exists)
    if not skip_existing or not Path(embeddings_path).exists() or Path(embeddings_path).stat().st_size == 0:
        embed_poems_task(input_path=processed_path, output_path=embeddings_path)
    else:
        print(f"🔹 Skipping embed – {embeddings_path} already exists")
    
    # 4. Ingest (always run – Qdrant may already have points, but we upsert new ones)
    ingest_count = ingest_poems_task(input_path=embeddings_path)
    
    return {"status": "success", "ingested": ingest_count}

if __name__ == "__main__":
    full_pipeline_flow()
