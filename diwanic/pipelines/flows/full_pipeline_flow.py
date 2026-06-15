"""Prefect flow for the full Diwanic pipeline."""
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
    embeddings_path: str = "data/embeddings/poems_with_embeddings.jsonl"
):
    """
    Orchestrate the Diwanic data pipeline:
    Scrape -> Preprocess -> Embed -> Ingest
    """
    # 1. Scrape
    scrape_poets_task(config_path=poets_config, max_poems_per_poet=max_poems, output_path=raw_path)
    
    # 2. Preprocess
    preprocess_poems_task(input_path=raw_path, output_path=processed_path)
    
    # 3. Embed
    embed_poems_task(input_path=processed_path, output_path=embeddings_path)
    
    # 4. Ingest
    ingest_count = ingest_poems_task(input_path=embeddings_path)
    
    return {"status": "success", "ingested": ingest_count}

if __name__ == "__main__":
    full_pipeline_flow()
